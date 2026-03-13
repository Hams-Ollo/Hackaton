#!/usr/bin/env python3
"""
sync-ado-workitems.py  (ado_backlog_pipeline bundle)
======================================================
Push CSV work item data → Azure DevOps.

Handles:
  - CREATE new items (blank "ID (ADO)") and write IDs back to CSV
  - UPDATE existing items (all planning/scheduling fields)
  - POST "Work Notes" column to System.History then clear the cell
  - Link parent-child relationships via "Parent ID (ADO)" column
  - Link Git branches via "Branch Name" / "Branch Repo" columns
  - Auto state-transition safety (New → Active → Closed two-hop)

.env: place your credentials in ado_backlog_pipeline/.env (copy .env.example → .env).

Usage
-----
  python sync-ado-workitems.py --dry-run          # print all actions, write nothing
  python sync-ado-workitems.py --report-only      # show CREATE/UPDATE intent only
  python sync-ado-workitems.py --row 3            # sync one row (1-based)
  python sync-ado-workitems.py --no-relations     # skip parent + branch linking
  python sync-ado-workitems.py                    # full live sync
"""

import os
import re
import sys
import csv
import json
import argparse
from pathlib import Path
from datetime import datetime
from urllib.parse import quote

# ---------------------------------------------------------------------------
# Path setup — ado_backlog_pipeline/scripts/ → bundle → workspace root
# ---------------------------------------------------------------------------
SCRIPT_DIR    = Path(__file__).resolve().parent        # .../ado_backlog_pipeline/scripts/
BUNDLE_DIR    = SCRIPT_DIR.parent                      # .../ado_backlog_pipeline/
WORKSPACE_DIR = BUNDLE_DIR.parent                      # repo root

CONFIG_PATH   = BUNDLE_DIR / "config" / "ado-config.yaml"
DATA_DIR      = BUNDLE_DIR / "data"

# .env: ado_backlog_pipeline/.env — copy .env.example and fill in ADO_PAT + ADO_ORG_URL
ENV_PATH = BUNDLE_DIR / ".env"

# ---------------------------------------------------------------------------
# Load .env
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv(ENV_PATH)
except ImportError:
    print("[WARN] python-dotenv not installed - reading env vars from shell only.")

# ---------------------------------------------------------------------------
# Third-party imports
# ---------------------------------------------------------------------------
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


def map_state(config: dict, wi_type: str, csv_state: str) -> str:
    state_map = config.get("state_map", {})
    type_map  = state_map.get(wi_type, state_map.get("default", {}))
    return type_map.get(csv_state, csv_state)


def _opt(ops: list, path: str, value) -> None:
    """Append a JsonPatchOperation only when value is non-blank."""
    if value is not None and str(value).strip() != "":
        ops.append(JsonPatchOperation(op="add", path=path, value=value))


def date_to_iso(mm_dd_yyyy: str) -> str | None:
    """Convert MM/DD/YYYY → YYYY-MM-DDT00:00:00Z.  Returns None on bad input."""
    s = str(mm_dd_yyyy).strip()
    if not s:
        return None
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%dT00:00:00Z")
        except ValueError:
            pass
    return None


def _int(val: str):
    try:
        return int(str(val).strip())
    except (ValueError, TypeError):
        return None


def _float(val: str):
    try:
        return float(str(val).strip())
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Build JSON Patch document for a CSV row
# ---------------------------------------------------------------------------
def build_patch_document(config: dict, row: dict) -> list[JsonPatchOperation]:
    wi_type  = row.get("Type", "").strip()
    project  = config["ado"]["project"]
    auto_tags = config.get("auto_tags", "csv-sync; adm-agentic")
    defaults  = config.get("field_defaults", {})

    # --- iteration / assignee resolution ------------------------------------
    iteration_map = config.get("iteration_map", {})
    assignee_map  = config.get("assignee_map", {})
    iteration_raw = row.get("Iteration #", "").strip()
    assignee_raw  = row.get("Assigned To (ADO)", "").strip()
    # Only resolve iterations we have an explicit mapping for.
    # Unknown/legacy values (old iterations, root bucket) are left unchanged in ADO.
    iteration_path = iteration_map.get(iteration_raw, "")
    assignee_email = assignee_map.get(assignee_raw, assignee_raw)

    # --- description assembly -----------------------------------------------
    description = row.get("Description", "").strip()
    comments    = row.get("Comments", "").strip()
    blocker     = row.get("Blocker/Dependency", "").strip()
    full_desc   = description
    if comments:
        full_desc += f"<br><br><b>Comments / Evidence:</b><br>{comments}"
    if blocker:
        full_desc += f"<br><br><b>Blocker / Dependency:</b><br>{blocker}"

    # --- tags merge ---------------------------------------------------------
    item_tags = row.get("Tags", "").strip()
    mvp_scope = row.get("In scope for DEMO or MVP Release?", "").strip().lower()
    all_tags_parts = [t.strip() for t in item_tags.split(";") if t.strip()] if item_tags else []
    if mvp_scope == "yes" and "mvp-scope" not in all_tags_parts:
        all_tags_parts.append("mvp-scope")
    for auto_tag in auto_tags.split(";"):
        t = auto_tag.strip()
        if t and t not in all_tags_parts:
            all_tags_parts.append(t)
    merged_tags = "; ".join(all_tags_parts)

    ops: list[JsonPatchOperation] = []

    # --- required fields ----------------------------------------------------
    _opt(ops, "/fields/System.Title",         row.get("Title", "").strip())
    _opt(ops, "/fields/System.Description",   full_desc)
    _opt(ops, "/fields/System.AssignedTo",    assignee_email)
    _opt(ops, "/fields/System.Tags",          merged_tags)
    _opt(ops, "/fields/System.IterationPath", iteration_path)

    # State is added to the doc but handled separately for two-hop transitions
    csv_state = row.get("State (ADO)", "").strip()
    ado_state = map_state(config, wi_type, csv_state)
    if ado_state:
        ops.append(JsonPatchOperation(op="add", path="/fields/System.State", value=ado_state))

    # --- planning fields ----------------------------------------------------
    priority = _int(row.get("Priority", "")) or _int(defaults.get("Priority"))
    _opt(ops, "/fields/Microsoft.VSTS.Common.Priority", priority)

    _opt(ops, "/fields/Microsoft.VSTS.Scheduling.StartDate",
         date_to_iso(row.get("Start (MM/DD/YYYY)", "")))
    _opt(ops, "/fields/Microsoft.VSTS.Scheduling.TargetDate",
         date_to_iso(row.get("End (MM/DD/YYYY)", "")))

    bv = _int(row.get("Business Value", ""))
    _opt(ops, "/fields/Microsoft.VSTS.Common.BusinessValue", bv)

    tc = _float(row.get("Time Criticality", ""))
    _opt(ops, "/fields/Microsoft.VSTS.Common.TimeCriticality", tc)

    # Effort → Epics and Features | Story Points → User Stories and Tasks
    if wi_type in ("Epic", "Feature"):
        effort = _float(row.get("Effort", ""))
        _opt(ops, "/fields/Microsoft.VSTS.Scheduling.Effort", effort)
    elif wi_type in ("User Story", "Task"):
        sp = _float(row.get("Story Points", ""))
        _opt(ops, "/fields/Microsoft.VSTS.Scheduling.StoryPoints", sp)

    # Risk → Epics, Features, User Stories
    if wi_type in ("Epic", "Feature", "User Story"):
        risk_val = row.get("Risk", "").strip() or defaults.get("Risk", "")
        _opt(ops, "/fields/Microsoft.VSTS.Common.Risk", risk_val)

    # Severity → Bugs only
    if wi_type == "Bug":
        sev_val = row.get("Severity", "").strip() or defaults.get("Severity", "")
        _opt(ops, "/fields/Microsoft.VSTS.Common.Severity", sev_val)

    # Blocked → Bugs and Tasks
    if wi_type in ("Bug", "Task"):
        blocked_val = row.get("Blocked", "").strip() or defaults.get("Blocked", "No")
        _opt(ops, "/fields/Microsoft.VSTS.CMMI.Blocked", blocked_val)

    # --- Work Notes → System.History ----------------------------------------
    work_notes = row.get("Work Notes", "").strip()
    if work_notes:
        ts  = datetime.now().strftime("%Y-%m-%d %H:%M")
        ops.append(JsonPatchOperation(
            op    = "add",
            path  = "/fields/System.History",
            value = f"{work_notes} <i>(logged {ts})</i>",
        ))

    return ops


# ---------------------------------------------------------------------------
# Resolve Git repo IDs (once at startup, cached)
# ---------------------------------------------------------------------------
_REPO_ID_CACHE: dict[str, str] = {}

def resolve_repo_ids(git_client, project: str, git_repos: dict) -> dict[str, str]:
    """Map short repo keys → actual ADO repository GUIDs."""
    global _REPO_ID_CACHE
    if _REPO_ID_CACHE:
        return _REPO_ID_CACHE
    try:
        all_repos = git_client.get_repositories(project)
        name_to_id = {r.name: r.id for r in all_repos}
        for short_key, repo_name in git_repos.items():
            rid = name_to_id.get(repo_name)
            if rid:
                _REPO_ID_CACHE[short_key] = rid
            else:
                print(f"  [WARN]  git_repos key '{short_key}' -> repo '{repo_name}' not found in ADO")
    except Exception as exc:
        print(f"  [WARN]  Could not resolve git repo IDs: {exc}")
    return _REPO_ID_CACHE


# ---------------------------------------------------------------------------
# Parent-child relation linking
# ---------------------------------------------------------------------------
def apply_parent_relation(
    wit_client, child_id: int, parent_id: int, org_url: str, project: str
) -> None:
    """Add Hierarchy-Reverse (parent) relation if not already linked. Idempotent."""
    try:
        existing = wit_client.get_work_item(child_id, expand="Relations")
        rels = existing.relations or []
        for rel in rels:
            if rel.rel == "System.LinkTypes.Hierarchy-Reverse":
                return  # already has a parent link
        parent_url = f"{org_url.rstrip('/')}/_apis/wit/workItems/{parent_id}"
        wit_client.update_work_item(
            document=[JsonPatchOperation(
                op    = "add",
                path  = "/relations/-",
                value = {"rel": "System.LinkTypes.Hierarchy-Reverse", "url": parent_url},
            )],
            id      = child_id,
            project = project,
        )
        print(f"    [LINKED]  #{child_id} -> parent #{parent_id}")
    except Exception as exc:
        print(f"    [WARN]  Parent link #{child_id} -> #{parent_id} failed: {exc}")


# ---------------------------------------------------------------------------
# Git branch linking
# ---------------------------------------------------------------------------
def apply_branch_link(
    wit_client, wi_id: int, repo_id: str, branch_name: str, project: str, org_url: str
) -> None:
    """Add ArtifactLink (Branch) relation if not already present. Idempotent."""
    try:
        ref_encoded = quote(f"refs/heads/{branch_name}", safe="")
        artifact_url = f"vstfs:///Git/Ref/{repo_id}/{ref_encoded}"

        existing = wit_client.get_work_item(wi_id, expand="Relations")
        rels = existing.relations or []
        for rel in rels:
            if getattr(rel, "url", "") == artifact_url:
                return  # already linked

        wit_client.update_work_item(
            document=[JsonPatchOperation(
                op    = "add",
                path  = "/relations/-",
                value = {
                    "rel":        "ArtifactLink",
                    "url":        artifact_url,
                    "attributes": {"name": "Branch"},
                },
            )],
            id      = wi_id,
            project = project,
        )
        print(f"    [BRANCH]  #{wi_id} -> {branch_name}")
    except Exception as exc:
        print(f"    [WARN]  Branch link #{wi_id} failed: {exc}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Push CSV work items → Azure DevOps")
    parser.add_argument("--dry-run",      action="store_true",
                        help="Print patch document without writing to ADO or CSV.")
    parser.add_argument("--report-only",  action="store_true",
                        help="Print CREATE/UPDATE intent only — no API calls.")
    parser.add_argument("--row",          type=int, default=None,
                        help="Sync only this 1-based row number (excluding header).")
    parser.add_argument("--no-relations",    action="store_true",
                        help="Skip parent and branch linking (safe for daily delta runs).")
    parser.add_argument("--relations-only",  action="store_true",
                        help="Apply parent and branch links only — skip all field updates and creates.")
    args = parser.parse_args()

    if args.relations_only and args.no_relations:
        print("[ERROR] --relations-only and --no-relations are mutually exclusive."); sys.exit(1)

    config   = load_config(CONFIG_PATH)
    org_url  = config["ado"]["org_url"]
    project  = config["ado"]["project"]
    git_repos = config.get("git_repos", {})
    pat      = os.environ.get("ADO_PAT", "")

    if not pat and not args.report_only and not args.dry_run and not args.relations_only:
        print("[ERROR] ADO_PAT not set. Copy ado_backlog_pipeline/.env.example → .env and set ADO_PAT.")
        sys.exit(1)

    csv_path = DATA_DIR / config.get("csv_path", "data/ado_azure_ai_search_work_items.csv").replace("data/", "")
    if not csv_path.exists():
        print(f"[ERROR] CSV not found: {csv_path}"); sys.exit(1)

    # --- Connect to ADO -----------------------------------------------------
    wit_client = None
    git_client = None
    if not args.report_only and not args.dry_run:
        credentials = BasicAuthentication("", pat)
        connection  = Connection(base_url=org_url, creds=credentials)
        wit_client  = connection.clients.get_work_item_tracking_client()
        if not args.no_relations and git_repos:
            git_client = connection.clients.get_git_client()
        print(f"[INFO] Connected to {org_url} / {project}")

    # --- Resolve repo IDs (once) --------------------------------------------
    repo_ids: dict[str, str] = {}
    if git_client and not args.no_relations:
        repo_ids = resolve_repo_ids(git_client, project, git_repos)

    relations_only = args.relations_only

    # --- Read CSV -----------------------------------------------------------
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader     = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows       = list(reader)

    total   = len(rows)
    created = updated = skipped = errors = 0
    notes_cleared: list[int] = []  # row indices where Work Notes were cleared
    dirty_cleared: list[int] = []  # row indices where _row_dirty was cleared

    mode_label = ("DRY-RUN" if args.dry_run
                  else "REPORT-ONLY" if args.report_only
                  else "RELATIONS-ONLY" if relations_only
                  else "LIVE")
    print(f"\n[INFO] {total} rows  |  {mode_label} mode\n")

    for i, row in enumerate(rows):
        row_num = i + 1
        if args.row is not None and row_num != args.row:
            continue

        wi_type = row.get("Type", "").strip()
        title   = row.get("Title", "").strip()
        ado_id  = row.get("ID (ADO)", "").strip()

        if not wi_type or not title:
            if not relations_only:
                print(f"  [SKIP]   Row {row_num:>3}: missing type or title")
                skipped += 1
            continue

        action = "CREATE" if not ado_id else f"UPDATE #{ado_id}"

        # --- Relations-only — skip all field work, jump straight to linking --
        if relations_only:
            if not ado_id:
                print(f"  [SKIP]   Row {row_num:>3}: no ADO ID — cannot link (run ado-sync first)")
                skipped += 1
                continue
            if not args.dry_run:
                parent_id_raw = row.get("Parent ID (ADO)", "").strip()
                if parent_id_raw:
                    try:
                        apply_parent_relation(
                            wit_client, int(ado_id), int(parent_id_raw), org_url, project
                        )
                    except ValueError:
                        print(f"    [WARN]  Row {row_num}: 'Parent ID (ADO)' value '{parent_id_raw}' is not a valid integer")
                branch_name = row.get("Branch Name", "").strip()
                branch_repo = row.get("Branch Repo", "").strip()
                if branch_name and branch_repo:
                    repo_id = repo_ids.get(branch_repo)
                    if repo_id:
                        apply_branch_link(wit_client, int(ado_id), repo_id, branch_name, project, org_url)
                    else:
                        print(f"    [WARN]  Row {row_num}: Branch Repo '{branch_repo}' not in git_repos config")
            else:
                parent_id_raw = row.get("Parent ID (ADO)", "").strip()
                branch_name   = row.get("Branch Name", "").strip()
                branch_repo   = row.get("Branch Repo", "").strip()
                if parent_id_raw or (branch_name and branch_repo):
                    print(f"  [DRY-RUN]  Row {row_num:>3}  #{ado_id:<6}  [{wi_type}]  {title[:45]}")
                    if parent_id_raw:
                        print(f"               parent link  -> #{parent_id_raw}")
                    if branch_name and branch_repo:
                        print(f"               branch link  -> {branch_repo}/{branch_name}")
            continue

        # --- Report-only ---------------------------------------------------
        if args.report_only:
            parent_id = row.get("Parent ID (ADO)", "").strip()
            parent_note = f"  parent->#{parent_id}" if parent_id else ""
            print(f"  [{action:<14}]  Row {row_num:>3}  [{wi_type:<12}]  "
                  f"[{map_state(config, wi_type, row.get('State (ADO)', ''))}]  "
                  f"{title[:50]}{parent_note}")
            continue

        # --- Build patch doc -----------------------------------------------
        patch_doc = build_patch_document(config, row)

        if args.dry_run:
            print(f"  [DRY-RUN]  Row {row_num:>3}  [{wi_type}]  {title[:55]}")
            for op in patch_doc:
                print(f"               {op.op:6}  {op.path:<50}  {str(op.value)[:50]}")
            continue

        # --- Live API calls ------------------------------------------------
        try:
            if not ado_id:
                # CREATE — omit State from initial call; apply via second PATCH
                create_doc = [op for op in patch_doc
                              if op.path not in ("/fields/System.State", "/fields/System.History")]
                wi = wit_client.create_work_item(document=create_doc, project=project, type=wi_type)
                new_id = wi.id
                rows[i]["ID (ADO)"] = str(new_id)
                created += 1
                dirty_cleared.append(i)
                print(f"  [CREATED]  Row {row_num:>3}  #{new_id:<6}  [{wi_type}]  {title[:55]}")

                # Two-hop state transition
                desired_state = next(
                    (op.value for op in patch_doc if op.path == "/fields/System.State"), None
                )
                if desired_state and desired_state != "New":
                    try:
                        if desired_state == "Closed":
                            wit_client.update_work_item(
                                document=[JsonPatchOperation(op="add", path="/fields/System.State", value="Active")],
                                id=new_id, project=project,
                            )
                        wit_client.update_work_item(
                            document=[JsonPatchOperation(op="add", path="/fields/System.State", value=desired_state)],
                            id=new_id, project=project,
                        )
                    except Exception as se:
                        print(f"    [WARN]  #{new_id} state -> {desired_state!r} failed: {se}")

                # Post Work Notes as history on newly created item
                history_op = next((op for op in patch_doc if op.path == "/fields/System.History"), None)
                if history_op:
                    try:
                        wit_client.update_work_item(
                            document=[history_op], id=new_id, project=project,
                        )
                        notes_cleared.append(i)
                    except Exception as ne:
                        print(f"    [WARN]  #{new_id} work notes post failed: {ne}")

                item_id_int = new_id

            else:
                # UPDATE
                wi = wit_client.update_work_item(
                    document=patch_doc, id=int(ado_id), project=project,
                )
                print(f"  [UPDATED]  Row {row_num:>3}  #{ado_id:<6}  [{wi_type}]  {title[:55]}")
                updated += 1
                dirty_cleared.append(i)
                # Mark Work Notes for clearing if they were posted
                if any(op.path == "/fields/System.History" for op in patch_doc):
                    notes_cleared.append(i)
                item_id_int = int(ado_id)

            # --- Relations -------------------------------------------------
            if not args.no_relations:
                parent_id_raw = row.get("Parent ID (ADO)", "").strip()
                if parent_id_raw:
                    try:
                        apply_parent_relation(
                            wit_client, item_id_int, int(parent_id_raw), org_url, project
                        )
                    except ValueError:
                        print(f"    [WARN]  Row {row_num}: 'Parent ID (ADO)' value '{parent_id_raw}' is not a valid integer")

                branch_name = row.get("Branch Name", "").strip()
                branch_repo = row.get("Branch Repo", "").strip()
                if branch_name and branch_repo:
                    repo_id = repo_ids.get(branch_repo)
                    if repo_id:
                        apply_branch_link(wit_client, item_id_int, repo_id, branch_name, project, org_url)
                    else:
                        print(f"    [WARN]  Row {row_num}: Branch Repo '{branch_repo}' not in git_repos config")

        except Exception as exc:
            print(f"  [ERROR]    Row {row_num:>3}  [{wi_type}]  {title[:40]}  ->  {exc}")
            errors += 1
            continue

    # --- Clear Work Notes in successfully synced rows -----------------------
    if notes_cleared:
        for idx in notes_cleared:
            rows[idx]["Work Notes"] = ""
        print(f"\n[INFO] Work Notes cleared for {len(notes_cleared)} row(s) "
              f"(successfully posted to ADO Discussion).")

    # --- Clear _row_dirty flag for successfully synced rows -----------------
    if dirty_cleared:
        for idx in dirty_cleared:
            if "_row_dirty" in rows[idx]:
                rows[idx]["_row_dirty"] = ""

    # --- Write CSV if any changes occurred ----------------------------------
    if not args.dry_run and not args.report_only and (created > 0 or notes_cleared or dirty_cleared):
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        print(f"[INFO] CSV updated - {created} new IDs written back, "
              f"{len(notes_cleared)} Work Notes cleared, "
              f"{len(dirty_cleared)} _row_dirty flags cleared -> {csv_path.name}")

    # --- Summary ------------------------------------------------------------
    print(f"\n{'='*60}")
    print(f"  Completed : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Created   : {created}")
    print(f"  Updated   : {updated}")
    print(f"  Skipped   : {skipped}")
    print(f"  Errors    : {errors}")
    print(f"{'='*60}\n")

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
