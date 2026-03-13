#!/usr/bin/env python3
"""
commit-ado-sync.py  (ado_backlog_pipeline bundle)
====================================================
Parse recent git commits, extract AB#ID references, then post comments +
state changes to ADO.

Supports cascade logic: when all child Tasks close → auto-close parent User Story,
when all User Stories close → auto-close parent Feature.

.env: place your credentials in ado_backlog_pipeline/.env (copy .env.example → .env).

Usage
-----
  python commit-ado-sync.py                        # commits since last push (default)
  python commit-ado-sync.py --dry-run              # print all actions, write nothing
  python commit-ado-sync.py --commits 10           # last 10 commits
  python commit-ado-sync.py --ids 1579 1580        # specific ADO IDs only
  python commit-ado-sync.py --no-cascade           # skip parent auto-close
  python commit-ado-sync.py --state-only           # post state change only, no History comment
  python commit-ado-sync.py --force-state Closed   # override inferred state
"""

import os
import re
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

SCRIPT_DIR    = Path(__file__).resolve().parent
BUNDLE_DIR    = SCRIPT_DIR.parent
WORKSPACE_DIR = BUNDLE_DIR.parent

CONFIG_PATH   = BUNDLE_DIR / "config" / "ado-config.yaml"

ENV_PATH = BUNDLE_DIR / ".env"

try:
    from dotenv import load_dotenv
    load_dotenv(ENV_PATH)
except ImportError:
    pass

try:
    import yaml
except ImportError:
    print("[ERROR] PyYAML not installed. Run: pip install pyyaml"); sys.exit(1)

try:
    from azure.devops.connection import Connection
    from azure.devops.v7_1.work_item_tracking.models import JsonPatchOperation
    from msrest.authentication import BasicAuthentication
except ImportError:
    print("[ERROR] azure-devops SDK not installed. Run: pip install azure-devops msrest"); sys.exit(1)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def load_config(path: Path) -> dict:
    if not path.exists():
        print(f"[ERROR] Config not found: {path}"); sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_commits_since_push(max_fallback: int = 10) -> list[dict]:
    """Return commits between local HEAD and upstream (@{u}). Falls back to last N."""
    try:
        result = subprocess.run(
            ["git", "log", "@{u}..HEAD", "--format=%H%x1F%s%x1F%b%x1F%aI"],
            capture_output=True, text=True, check=True, cwd=WORKSPACE_DIR,
        )
        return _parse_git_log(result.stdout)
    except subprocess.CalledProcessError:
        # No upstream configured — fall back to last N commits
        result = subprocess.run(
            ["git", "log", f"-{max_fallback}", "--format=%H%x1F%s%x1F%b%x1F%aI"],
            capture_output=True, text=True, cwd=WORKSPACE_DIR,
        )
        return _parse_git_log(result.stdout)


def get_last_n_commits(n: int) -> list[dict]:
    result = subprocess.run(
        ["git", "log", f"-{n}", "--format=%H%x1F%s%x1F%b%x1F%aI"],
        capture_output=True, text=True, cwd=WORKSPACE_DIR,
    )
    return _parse_git_log(result.stdout)


def _parse_git_log(raw: str) -> list[dict]:
    commits = []
    for line in raw.strip().splitlines():
        parts = line.split("\x1f")
        if len(parts) >= 2:
            commits.append({
                "hash":    parts[0][:8] if parts[0] else "",
                "subject": parts[1] if len(parts) > 1 else "",
                "body":    parts[2] if len(parts) > 2 else "",
                "date":    parts[3][:10] if len(parts) > 3 else "",
            })
    return commits


def extract_ab_ids(commits: list[dict]) -> dict[int, list[dict]]:
    """Map ADO ID → list of commits referencing it."""
    id_map: dict[int, list[dict]] = {}
    for commit in commits:
        text = commit["subject"] + " " + commit["body"]
        for m in re.finditer(r"AB#(\d+)", text, re.IGNORECASE):
            wi_id = int(m.group(1))
            id_map.setdefault(wi_id, []).append(commit)
    return id_map


def infer_state(commits: list[dict], keywords: list[str]) -> str | None:
    """Return 'Closed' if a state keyword precedes AB#ID, else None."""
    kw_pattern = "|".join(re.escape(k) for k in keywords)
    for commit in commits:
        text = (commit["subject"] + " " + commit["body"]).lower()
        if re.search(rf"\b({kw_pattern})\b.*ab#\d+|ab#\d+.*\b({kw_pattern})\b", text):
            return "Closed"
    return None


# ---------------------------------------------------------------------------
# Cascade logic
# ---------------------------------------------------------------------------
def check_cascade(
    wit_client, closed_ids: set[int], project: str, org_url: str,
    dry_run: bool = False
) -> list[int]:
    """
    For each closed item, check if all siblings are also closed.
    If so, auto-close the parent. Returns list of auto-closed parent IDs.
    """
    auto_closed: list[int] = []

    def try_cascade(child_ids: set[int]) -> None:
        parent_ids_to_check: set[int] = set()
        for child_id in child_ids:
            try:
                wi = wit_client.get_work_item(child_id, expand="Relations")
                for rel in (wi.relations or []):
                    if rel.rel == "System.LinkTypes.Hierarchy-Reverse":
                        m = re.search(r"/(\d+)$", rel.url)
                        if m:
                            parent_ids_to_check.add(int(m.group(1)))
            except Exception:
                pass

        for parent_id in parent_ids_to_check:
            try:
                parent_wi = wit_client.get_work_item(parent_id, expand="Relations")
                parent_state = (parent_wi.fields or {}).get("System.State", "")
                if parent_state in ("Closed", "Done"):
                    continue
                parent_type = (parent_wi.fields or {}).get("System.WorkItemType", "")

                # Collect all child IDs
                child_rels = [
                    r for r in (parent_wi.relations or [])
                    if r.rel == "System.LinkTypes.Hierarchy-Forward"
                ]
                if not child_rels:
                    continue

                child_id_list = []
                for r in child_rels:
                    m = re.search(r"/(\d+)$", r.url)
                    if m:
                        child_id_list.append(int(m.group(1)))

                # Batch fetch child states
                if not child_id_list:
                    continue
                children = wit_client.get_work_items(
                    ids=child_id_list, fields=["System.State"], error_policy="omit"
                )
                all_closed = all(
                    (c.fields or {}).get("System.State", "") in ("Closed", "Done")
                    for c in children if c
                )

                if all_closed:
                    ts   = datetime.now().strftime("%Y-%m-%d %H:%M")
                    note = (
                        f"Auto-closed: all child {parent_type}s are now Closed. "
                        f"<i>(cascade from AB#{', AB#'.join(str(x) for x in sorted(child_ids))} "
                        f"— {ts})</i>"
                    )
                    if not dry_run:
                        # New → Active hop if needed
                        if parent_state == "New":
                            wit_client.update_work_item(
                                document=[JsonPatchOperation(
                                    op="add", path="/fields/System.State", value="Active"
                                )],
                                id=parent_id, project=project,
                            )
                        wit_client.update_work_item(
                            document=[
                                JsonPatchOperation(op="add", path="/fields/System.State",
                                                   value="Closed"),
                                JsonPatchOperation(op="add", path="/fields/System.History",
                                                   value=note),
                            ],
                            id=parent_id, project=project,
                        )
                    print(f"  [CASCADE]  #{parent_id}  [{parent_type}]  -> Closed "
                          f"(all children closed){' [DRY-RUN]' if dry_run else ''}")
                    auto_closed.append(parent_id)
            except Exception as exc:
                print(f"  [WARN]  Cascade check for parent #{parent_id} failed: {exc}")

    try_cascade(closed_ids)
    # Second-level cascade (e.g. Feature after User Stories close)
    if auto_closed:
        try_cascade(set(auto_closed))

    return auto_closed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Sync git commits → ADO work item comments & state"
    )
    parser.add_argument("--dry-run",      action="store_true",
                        help="Print all actions without writing to ADO.")
    parser.add_argument("--since-push",   action="store_true", default=True,
                        help="Process commits not yet on remote (default).")
    parser.add_argument("--commits",      type=int, default=None,
                        help="Process last N commits instead of since-push.")
    parser.add_argument("--ids",          type=int, nargs="+", default=None,
                        help="Target specific ADO IDs (skip commit parsing).")
    parser.add_argument("--no-cascade",   action="store_true",
                        help="Skip parent auto-close cascade logic.")
    parser.add_argument("--state-only",   action="store_true",
                        help="Post state change only — skip adding a System.History comment.")
    parser.add_argument("--force-state",  default=None,
                        help="Override inferred state (e.g. --force-state Closed).")
    args = parser.parse_args()

    config     = load_config(CONFIG_PATH)
    org_url    = config["ado"]["org_url"]
    project    = config["ado"]["project"]
    sync_cfg   = config.get("commit_sync", {})
    keywords   = sync_cfg.get("state_keywords", ["fixes", "closes", "resolves"])
    cascade_on = sync_cfg.get("cascade_enabled", True) and not args.no_cascade
    fallback_n = sync_cfg.get("default_commit_lookback", 10)

    pat = os.environ.get("ADO_PAT", "")
    if not pat and not args.dry_run:
        print("[ERROR] ADO_PAT not set."); sys.exit(1)

    # --- Gather commits and extract AB# IDs --------------------------------
    if args.ids:
        # Manual ID mode — no commit parsing needed
        id_commit_map: dict[int, list[dict]] = {wi_id: [] for wi_id in args.ids}
        print(f"[INFO] Manual mode — targeting {len(args.ids)} item(s): {args.ids}")
    else:
        if args.commits:
            commits = get_last_n_commits(args.commits)
        else:
            commits = get_commits_since_push(max_fallback=fallback_n)

        if not commits:
            print("[INFO] No commits found to process."); return

        id_commit_map = extract_ab_ids(commits)
        if not id_commit_map:
            print(f"[INFO] No AB#ID references found in {len(commits)} commit(s)."); return

        print(f"[INFO] {len(commits)} commit(s) -> {len(id_commit_map)} unique ADO ID(s) found: "
              f"{sorted(id_commit_map.keys())}")

    # --- Connect to ADO ----------------------------------------------------
    if not args.dry_run:
        credentials = BasicAuthentication("", pat)
        connection  = Connection(base_url=org_url, creds=credentials)
        wit_client  = connection.clients.get_work_item_tracking_client()
    else:
        wit_client = None

    # --- Process each discovered ADO item -----------------------------------
    closed_ids: set[int] = set()
    success = errors = 0

    print()
    for wi_id, item_commits in sorted(id_commit_map.items()):
        # Fetch current item context from ADO
        wi_type = wi_title = wi_state = "unknown"
        if not args.dry_run:
            try:
                wi = wit_client.get_work_item(wi_id)
                f  = wi.fields or {}
                wi_type  = f.get("System.WorkItemType", "unknown")
                wi_title = f.get("System.Title", "unknown")
                wi_state = f.get("System.State", "unknown")
            except Exception as exc:
                print(f"  [ERROR]  #{wi_id} fetch failed: {exc}"); errors += 1; continue

        # Infer state change
        new_state = args.force_state
        if not new_state and item_commits:
            inferred = infer_state(item_commits, keywords)
            if inferred and wi_state not in ("Closed", "Done"):
                new_state = inferred
            elif wi_state == "New" and item_commits:
                new_state = "Active"

        # Generate work note from raw commit text
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        if not args.state_only:
            commit_lines = "; ".join(
                f"[{c['hash']}] {c['subject']}" for c in item_commits
            ) if item_commits else "(manual update)"
            note      = f"Work update: {commit_lines}"
            note_html = f"{note} <i>({ts})</i>"

        if args.dry_run:
            note_preview = note[:100] if not args.state_only else "(state only — no comment)"
            print(f"  [DRY-RUN]  #{wi_id}  [{wi_type}]  {str(wi_title)[:45]}")
            print(f"               State: {wi_state} -> {new_state or 'no change'}")
            print(f"               Note:  {note_preview}...")
            continue

        # Build patch and apply
        patch_ops = []
        if not args.state_only:
            patch_ops.append(JsonPatchOperation(op="add", path="/fields/System.History", value=note_html))
        if new_state and new_state != wi_state:
            # Two-hop safety for Closed
            try:
                if new_state == "Closed" and wi_state == "New":
                    wit_client.update_work_item(
                        document=[JsonPatchOperation(
                            op="add", path="/fields/System.State", value="Active"
                        )],
                        id=wi_id, project=project,
                    )
                if new_state == "Closed" and wi_state in ("New", "Active"):
                    patch_ops.append(
                        JsonPatchOperation(op="add", path="/fields/System.State", value="Closed")
                    )
                elif new_state != "Closed":
                    patch_ops.append(
                        JsonPatchOperation(op="add", path="/fields/System.State", value=new_state)
                    )
            except Exception as exc:
                print(f"    [WARN]  #{wi_id} state pre-hop failed: {exc}")

        try:
            wit_client.update_work_item(document=patch_ops, id=wi_id, project=project)
            state_note = f" -> {new_state}" if new_state and new_state != wi_state else ""
            print(f"  [UPDATED]  #{wi_id}  [{wi_type}]{state_note}  {str(wi_title)[:45]}")
            success += 1
            if new_state == "Closed" or wi_state in ("Closed", "Done"):
                closed_ids.add(wi_id)
        except Exception as exc:
            print(f"  [ERROR]    #{wi_id}  {exc}"); errors += 1

    # --- Cascade -----------------------------------------------------------
    if cascade_on and closed_ids and not args.dry_run:
        print(f"\n[INFO] Running cascade check for {len(closed_ids)} closed item(s)...")
        check_cascade(wit_client, closed_ids, project, org_url, dry_run=False)
    elif cascade_on and closed_ids and args.dry_run:
        print(f"\n[DRY-RUN] Cascade check would run for: {sorted(closed_ids)}")

    # --- Summary -----------------------------------------------------------
    print(f"\n{'='*55}")
    print(f"  Completed : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Updated   : {success}")
    print(f"  Errors    : {errors}")
    print(f"  Cascaded  : {len(closed_ids)} item(s) checked")
    print(f"{'='*55}\n")

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
