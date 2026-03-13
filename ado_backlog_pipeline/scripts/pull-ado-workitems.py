#!/usr/bin/env python3
"""
pull-ado-workitems.py  (ado_backlog_pipeline bundle)
=======================================================
Pull Azure DevOps work items → CSV (morning sync / incremental refresh).

Merges fetched ADO data into the local CSV, preserving protected columns
(Work Notes, Owner, Dev Lead, etc.) that are managed locally.

.env: place your credentials in ado_backlog_pipeline/.env (copy .env.example → .env).

Usage
-----
  # Pull your items changed since yesterday (default)
  python pull-ado-workitems.py

  # Dry-run — print what would be written, no CSV changes
  python pull-ado-workitems.py --dry-run

  # Incremental — only items changed since a date
  python pull-ado-workitems.py --since 2026-02-19

  # Full sprint pull for a specific iteration
  python pull-ado-workitems.py --iteration "ADM-Agentic\\Iteration 9" --all

  # Pull specific items by ID
  python pull-ado-workitems.py --ids 1534 1569 1560

  # Pull all items regardless of assignee
  python pull-ado-workitems.py --all

  # Also overwrite Work Notes column (use when starting a new sprint)
  python pull-ado-workitems.py --overwrite-notes
"""

import os
import sys
import csv
import html
import re
import argparse
from pathlib import Path
from datetime import datetime, timezone

SCRIPT_DIR    = Path(__file__).resolve().parent
BUNDLE_DIR    = SCRIPT_DIR.parent
WORKSPACE_DIR = BUNDLE_DIR.parent

CONFIG_PATH   = BUNDLE_DIR / "config" / "ado-config.yaml"
DATA_DIR      = BUNDLE_DIR / "data"

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
    from azure.devops.v7_1.work_item_tracking.models import Wiql, TeamContext
    from msrest.authentication import BasicAuthentication
except ImportError:
    print("[ERROR] azure-devops SDK not installed. Run: pip install azure-devops msrest"); sys.exit(1)

# ---------------------------------------------------------------------------
# Canonical 43-column CSV header (single source of truth for this bundle)
# Mirrors the fields section in ado-config.yaml — update both together.
# ---------------------------------------------------------------------------
CANONICAL_FIELDNAMES = [
    # Identity
    "ID (ADO)",
    "Type",
    "Parent ID (ADO)",
    "Title",
    "Area Path",
    "Iteration #",
    # Planning
    "Priority",
    "Backlog Priority",
    "Story Points",
    "Effort",
    "Business Value",
    "Time Criticality",
    "Risk",
    "Severity",
    # Scheduling
    "Start (MM/DD/YYYY)",
    "End (MM/DD/YYYY)",
    # State & Board
    "State (ADO)",
    "Reason",
    "Blocked",
    "Board Column",
    "Board Lane",
    # Audit Dates
    "Created Date (ADO)",
    "Changed Date (ADO)",
    "State Changed Date (ADO)",
    "Activated Date (ADO)",
    "Resolved Date (ADO)",
    "Closed Date (ADO)",
    # Assignment & Tags
    "Assigned To (ADO)",
    "Tags",
    # Counts
    "Comment Count",
    "Related Link Count",
    # Content
    "Description",
    # Local-only
    "Status",
    "Owner",
    "Dev Lead",
    "Work Notes",
    "Comments",
    "Blocker/Dependency",
    "Branch Name",
    "Branch Repo",
    "In scope for DEMO or MVP Release?",
    # Meta
    "Last Synced (ADO)",
    "_row_dirty",
]

# ADO fields to fetch in one batch call — includes all non-local columns
ADO_FIELDS = [
    # Identity
    "System.Id",
    "System.WorkItemType",
    "System.Parent",
    "System.Title",
    "System.AreaPath",
    "System.IterationPath",
    # Planning
    "Microsoft.VSTS.Common.Priority",
    "Microsoft.VSTS.Common.BacklogPriority",
    "Microsoft.VSTS.Scheduling.StoryPoints",
    "Microsoft.VSTS.Scheduling.Effort",
    "Microsoft.VSTS.Common.BusinessValue",
    "Microsoft.VSTS.Common.TimeCriticality",
    "Microsoft.VSTS.Common.Risk",
    "Microsoft.VSTS.Common.Severity",
    # Scheduling
    "Microsoft.VSTS.Scheduling.StartDate",
    "Microsoft.VSTS.Scheduling.TargetDate",
    # State & Board
    "System.State",
    "System.Reason",
    "Microsoft.VSTS.CMMI.Blocked",
    "System.BoardColumn",
    "System.BoardLane",
    # Audit Dates
    "System.CreatedDate",
    "System.ChangedDate",
    "Microsoft.VSTS.Common.StateChangeDate",
    "Microsoft.VSTS.Common.ActivatedDate",
    "Microsoft.VSTS.Common.ResolvedDate",
    "Microsoft.VSTS.Common.ClosedDate",
    # Assignment & Tags
    "System.AssignedTo",
    "System.Tags",
    # Counts
    "System.CommentCount",
    "System.RelatedLinkCount",
    # Content
    "System.Description",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def load_config(path: Path) -> dict:
    if not path.exists():
        print(f"[ERROR] Config not found: {path}"); sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def iso_to_date(iso_str: str) -> str:
    """Convert ISO 8601 datetime string → MM/DD/YYYY. Returns '' on bad input."""
    if not iso_str:
        return ""
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(iso_str[:19].replace("T", " ").rstrip(" "), fmt.replace("T%H:%M:%S", "").replace("Z","") if len(iso_str) <= 10 else fmt).strftime("%m/%d/%Y")
        except ValueError:
            pass
    # Fallback: try parsing just the date portion
    try:
        return datetime.strptime(iso_str[:10], "%Y-%m-%d").strftime("%m/%d/%Y")
    except ValueError:
        return ""


def derive_status(ado_state: str) -> str:
    return "Closed" if ado_state in ("Closed", "Done", "Resolved") else "Active"


def ado_state_to_csv(ado_state: str, config: dict, wi_type: str) -> str:
    """Reverse map ADO state → CSV State (ADO) column value."""
    state_map = config.get("state_map", {})
    type_map  = state_map.get(wi_type, state_map.get("default", {}))
    reverse   = {v: k for k, v in type_map.items()}
    return reverse.get(ado_state, ado_state)


def build_iteration_reverse_map(config: dict) -> dict[str, str]:
    """Build full-path → shorthand lookup from iteration_map."""
    return {v: k for k, v in config.get("iteration_map", {}).items()}


def build_assignee_reverse_map(config: dict) -> dict[str, str]:
    """Build email → display name lookup from assignee_map."""
    return {v: k for k, v in config.get("assignee_map", {}).items()}


def map_wi_to_row(wi, config: dict, iter_reverse: dict, assign_reverse: dict) -> dict:
    """Convert an ADO work item object to a canonical CSV row dict."""
    f = wi.fields or {}

    assignee_raw  = f.get("System.AssignedTo", "")
    assignee_email = (
        assignee_raw.get("uniqueName", assignee_raw.get("displayName", str(assignee_raw)))
        if isinstance(assignee_raw, dict) else str(assignee_raw)
    )
    assignee_display = assign_reverse.get(assignee_email, assignee_email)

    wi_type   = f.get("System.WorkItemType", "")
    ado_state = f.get("System.State", "")

    iter_path  = f.get("System.IterationPath", "")
    iter_short = iter_reverse.get(iter_path, iter_path.split("\\")[-1] if iter_path else "")

    parent_id_raw = f.get("System.Parent", "")
    parent_id = str(int(parent_id_raw)) if parent_id_raw else ""

    synced_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Strip HTML tags then decode entities (&amp; &nbsp; &lt; etc.)
    raw_desc  = f.get("System.Description", "") or ""
    clean_desc = html.unescape(re.sub(r"<[^>]+>", " ", raw_desc)).strip()
    clean_desc = re.sub(r"[ \t]{2,}", " ", re.sub(r"\n{3,}", "\n\n", clean_desc))

    def _iso_date(key: str) -> str:
        """Return YYYY-MM-DD from an ADO ISO 8601 datetime field, or ''."""
        val = str(f.get(key, "") or "")
        return val[:10] if val else ""

    return {
        # Identity
        "ID (ADO)":                              str(wi.id),
        "Type":                                  wi_type,
        "Parent ID (ADO)":                       parent_id,
        "Title":                                 f.get("System.Title", ""),
        "Area Path":                             f.get("System.AreaPath", ""),
        "Iteration #":                           iter_short,
        # Planning
        "Priority":                              str(f.get("Microsoft.VSTS.Common.Priority", "") or ""),
        "Backlog Priority":                      str(f.get("Microsoft.VSTS.Common.BacklogPriority", "") or ""),
        "Story Points":                          str(f.get("Microsoft.VSTS.Scheduling.StoryPoints", "") or ""),
        "Effort":                                str(f.get("Microsoft.VSTS.Scheduling.Effort", "") or ""),
        "Business Value":                        str(f.get("Microsoft.VSTS.Common.BusinessValue", "") or ""),
        "Time Criticality":                      str(f.get("Microsoft.VSTS.Common.TimeCriticality", "") or ""),
        "Risk":                                  str(f.get("Microsoft.VSTS.Common.Risk", "") or ""),
        "Severity":                              str(f.get("Microsoft.VSTS.Common.Severity", "") or ""),
        # Scheduling
        "Start (MM/DD/YYYY)":                    iso_to_date(str(f.get("Microsoft.VSTS.Scheduling.StartDate", "") or "")),
        "End (MM/DD/YYYY)":                      iso_to_date(str(f.get("Microsoft.VSTS.Scheduling.TargetDate", "") or "")),
        # State & Board
        "State (ADO)":                           ado_state_to_csv(ado_state, config, wi_type),
        "Reason":                                f.get("System.Reason", "") or "",
        "Blocked":                               str(f.get("Microsoft.VSTS.CMMI.Blocked", "") or ""),
        "Board Column":                          f.get("System.BoardColumn", "") or "",
        "Board Lane":                            f.get("System.BoardLane", "") or "",
        # Audit Dates
        "Created Date (ADO)":                    _iso_date("System.CreatedDate"),
        "Changed Date (ADO)":                    _iso_date("System.ChangedDate"),
        "State Changed Date (ADO)":              _iso_date("Microsoft.VSTS.Common.StateChangeDate"),
        "Activated Date (ADO)":                  _iso_date("Microsoft.VSTS.Common.ActivatedDate"),
        "Resolved Date (ADO)":                   _iso_date("Microsoft.VSTS.Common.ResolvedDate"),
        "Closed Date (ADO)":                     _iso_date("Microsoft.VSTS.Common.ClosedDate"),
        # Assignment & Tags
        "Assigned To (ADO)":                     assignee_display,
        "Tags":                                  f.get("System.Tags", "") or "",
        # Counts
        "Comment Count":                         str(f.get("System.CommentCount", "") or ""),
        "Related Link Count":                    str(f.get("System.RelatedLinkCount", "") or ""),
        # Content
        "Description":                           clean_desc,
        # Local-only — preserved from existing row in merge logic
        "Status":                                derive_status(ado_state),
        "Owner":                                 "",
        "Dev Lead":                              "",
        "Work Notes":                            "",
        "Comments":                              "",
        "Blocker/Dependency":                    "",
        "Branch Name":                           "",
        "Branch Repo":                           "",
        "In scope for DEMO or MVP Release?":     "",
        # Meta
        "Last Synced (ADO)":                     synced_ts,
        "_row_dirty":                            "",
    }


def build_wiql(project: str, assignee_email: str | None, iteration: str | None,
               since: str | None, fetch_all: bool) -> str:
    conditions = [f"[System.TeamProject] = '{project}'"]
    if not fetch_all and assignee_email:
        conditions.append(f"[System.AssignedTo] = '{assignee_email}'")
    if iteration:
        conditions.append(f"[System.IterationPath] UNDER '{iteration}'")
    if since:
        conditions.append(f"[System.ChangedDate] >= '{since}'")
    where = " AND ".join(conditions)
    fields_clause = ", ".join(f"[{f}]" for f in ADO_FIELDS)
    return (
        f"SELECT {fields_clause} FROM workitems "
        f"WHERE {where} ORDER BY [System.ChangedDate] DESC"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Pull ADO work items → local CSV")
    parser.add_argument("--dry-run",         action="store_true",
                        help="Print changes without writing to CSV.")
    parser.add_argument("--all",             action="store_true",
                        help="Pull all items (ignore assignee filter).")
    parser.add_argument("--assignee",        default=None,
                        help="Filter by assignee display name (from assignee_map). "
                             "Defaults to pull.default_assignee in config.")
    parser.add_argument("--iteration",       default=None,
                        help="Filter to items UNDER this iteration path.")
    parser.add_argument("--since",           default=None,
                        help="Only items changed since YYYY-MM-DD.")
    parser.add_argument("--ids",             type=int, nargs="+", default=None,
                        help="Pull specific work item IDs only.")
    parser.add_argument("--overwrite-notes", action="store_true",
                        help="Also overwrite Work Notes column (use at sprint start).")
    args = parser.parse_args()

    config  = load_config(CONFIG_PATH)
    org_url = config["ado"]["org_url"]
    project = config["ado"]["project"]
    pat     = os.environ.get("ADO_PAT", "")

    if not pat and not args.dry_run:
        print("[ERROR] ADO_PAT not set."); sys.exit(1)

    pull_cfg         = config.get("pull", {})
    protected_cols   = pull_cfg.get("protected_columns", ["Work Notes"])
    if args.overwrite_notes and "Work Notes" in protected_cols:
        protected_cols = [c for c in protected_cols if c != "Work Notes"]

    default_assignee = pull_cfg.get("default_assignee", "")
    assignee_label   = args.assignee or (None if args.all else default_assignee)
    assignee_map     = config.get("assignee_map", {})
    assignee_email   = assignee_map.get(assignee_label, assignee_label) if assignee_label else None

    iter_reverse  = build_iteration_reverse_map(config)
    assign_reverse = build_assignee_reverse_map(config)

    csv_path = DATA_DIR / config.get("csv_path", "data/ado_azure_ai_search_work_items.csv").replace("data/", "")

    # --- Load existing CSV --------------------------------------------------
    existing_rows: dict[str, dict] = {}
    existing_fieldnames = CANONICAL_FIELDNAMES[:]

    if csv_path.exists():
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            existing_fieldnames = list(reader.fieldnames or CANONICAL_FIELDNAMES)
            for row in reader:
                wi_id = row.get("ID (ADO)", "").strip()
                if wi_id:
                    existing_rows[wi_id] = dict(row)
        # Ensure all canonical columns exist (migration from old header)
        for col in CANONICAL_FIELDNAMES:
            if col not in existing_fieldnames:
                existing_fieldnames.append(col)

    # --- Connect to ADO -----------------------------------------------------
    if not args.dry_run:
        credentials = BasicAuthentication("", pat)
        connection  = Connection(base_url=org_url, creds=credentials)
        wit_client  = connection.clients.get_work_item_tracking_client()
        print(f"[INFO] Connected to {org_url} / {project}")
    else:
        print(f"[INFO] DRY-RUN mode — no changes will be written")
        wit_client = None

    # --- Fetch work items ---------------------------------------------------
    fetched_items: list = []

    if args.ids:
        print(f"[INFO] Fetching {len(args.ids)} specific item(s)...")
        if not args.dry_run:
            batch = wit_client.get_work_items(ids=args.ids, fields=ADO_FIELDS,
                                              error_policy="omit")
            fetched_items = [wi for wi in batch if wi is not None]
    else:
        wiql_str = build_wiql(project, assignee_email, args.iteration, args.since,
                               args.all)
        if args.dry_run:
            print(f"\n[DRY-RUN]  WIQL query that would be executed:")
            print(f"  {wiql_str}\n")
            print(f"  Existing CSV rows: {len(existing_rows)}")
            print(f"  Protected columns: {protected_cols}")
            return

        print(f"[INFO] Executing WIQL query...")
        team_context = TeamContext(project=project)
        result       = wit_client.query_by_wiql(Wiql(query=wiql_str), team_context=team_context)
        wi_refs      = result.work_items or []

        if not wi_refs:
            print("[INFO] No work items matched the query."); return

        print(f"[INFO] Fetching fields for {len(wi_refs)} item(s)...")
        ids           = [r.id for r in wi_refs]
        # Batch in chunks of 200 (ADO API limit)
        for chunk_start in range(0, len(ids), 200):
            chunk = ids[chunk_start:chunk_start + 200]
            batch = wit_client.get_work_items(ids=chunk, fields=ADO_FIELDS,
                                              error_policy="omit")
            fetched_items.extend(wi for wi in batch if wi is not None)

    # --- Merge into existing CSV rows ---------------------------------------
    pulled = updated = added = preserved = 0

    for wi in fetched_items:
        if wi is None:
            continue
        pulled     += 1
        new_data    = map_wi_to_row(wi, config, iter_reverse, assign_reverse)
        wi_id_str   = str(wi.id)

        if wi_id_str in existing_rows:
            existing = existing_rows[wi_id_str]
            # Preserve protected columns from existing row
            for col in protected_cols:
                if col in existing and existing[col].strip():
                    new_data[col] = existing[col]
                    preserved += 1
            # Preserve other local-only cols that have values (not in ADO)
            for local_col in ["Blocker/Dependency", "Comments", "Owner", "Dev Lead",
                               "In scope for DEMO or MVP Release?", "Branch Name",
                               "Branch Repo", "Status", "_row_dirty"]:
                if local_col not in protected_cols:
                    existing_val = existing.get(local_col, "").strip()
                    if existing_val:
                        new_data[local_col] = existing_val
            existing_rows[wi_id_str] = new_data
            updated += 1
        else:
            existing_rows[wi_id_str] = new_data
            added += 1

    # --- Print dry-run preview or summary -----------------------------------
    print(f"\n[INFO] Pull results: {pulled} fetched | {updated} updated | "
          f"{added} new | {preserved} protected field(s) preserved")

    if args.dry_run:
        print("\n[DRY-RUN] First 5 rows that would be written:")
        for row in list(existing_rows.values())[:5]:
            print(f"  #{row.get('ID (ADO)'):>5}  [{row.get('Type'):<12}]  "
                  f"{row.get('Title', '')[:55]}")
        return

    # --- Write updated CSV --------------------------------------------------
    # Re-order rows to preserve original order + append new items at bottom
    ordered_rows = []
    seen_ids     = set()

    if csv_path.exists():
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            old_rows = list(csv.DictReader(f))
        for old_row in old_rows:
            wi_id = old_row.get("ID (ADO)", "").strip()
            if wi_id in existing_rows:
                merged = {col: existing_rows[wi_id].get(col, old_row.get(col, ""))
                          for col in existing_fieldnames}
                ordered_rows.append(merged)
                seen_ids.add(wi_id)
            else:
                # Row not returned by ADO query (out of filter scope) — preserve as-is
                ordered_rows.append({col: old_row.get(col, "") for col in existing_fieldnames})
                if wi_id:
                    seen_ids.add(wi_id)

    # Append truly new items not in original CSV
    for wi_id, row_data in existing_rows.items():
        if wi_id not in seen_ids:
            ordered_rows.append({col: row_data.get(col, "") for col in existing_fieldnames})

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=existing_fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(ordered_rows)

    print(f"[INFO] CSV updated -> {csv_path.name}  "
          f"({len(ordered_rows)} total rows)\n")


if __name__ == "__main__":
    main()
