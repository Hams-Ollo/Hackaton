"""
set-priority.py
───────────────
Scan the backlog CSV and fill in any blank Priority cells using the type-based
defaults configured in ado-config.yaml (priority_defaults section).

Only fills **blank** cells — existing values are never overwritten.
Run this after adding new work items, before syncing to ADO.

Usage:
  python scripts/set-priority.py              # fill all blank priorities (open items)
  python scripts/set-priority.py --dry-run    # preview changes, no file write
  python scripts/set-priority.py --all        # include closed/done items too
  python scripts/set-priority.py --report     # list gaps only, no changes made
  python scripts/set-priority.py --ids 1601 1607 1608
  python scripts/set-priority.py --type Task

Priority scale: 1=Critical  2=High  3=Medium  4=Low
Defaults are set per work item type in config/ado-config.yaml.
After running, use ado-sync (sync-ado-workitems.py) to push to ADO.
"""

import argparse
import csv
import sys
from pathlib import Path

from dotenv import load_dotenv
import yaml

# ---------------------------------------------------------------------------
# Bundle path setup  (same pattern as all other pipeline scripts)
# ---------------------------------------------------------------------------
BUNDLE_DIR = Path(__file__).resolve().parent.parent
_env_path  = BUNDLE_DIR / ".env"
load_dotenv(_env_path)

OPEN_STATES = {"In Progress", "Not Started", "Active", "New"}


def load_config() -> dict:
    cfg_path = BUNDLE_DIR / "config" / "ado-config.yaml"
    with open(cfg_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fill blank Priority values in the backlog CSV using type-based defaults"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview changes without writing to the CSV")
    parser.add_argument("--all",     action="store_true",
                        help="Process all items including closed/done (default: open only)")
    parser.add_argument("--report",  action="store_true",
                        help="List items with no priority set — do not apply changes")
    parser.add_argument("--ids",     nargs="+", metavar="ID",
                        help="Only process these specific ADO IDs")
    parser.add_argument("--type",    metavar="TYPE",
                        help="Filter by work item type, e.g. Task, Feature")
    args = parser.parse_args()

    config = load_config()
    priority_defaults: dict = config.get("priority_defaults", {})

    if not priority_defaults:
        print("[WARN] No 'priority_defaults' section found in ado-config.yaml.")
        print("       Add the section — see the config file for the format.")
        sys.exit(1)

    fallback_priority = str(priority_defaults.get("default", 2))
    type_map: dict = priority_defaults.get("by_type", {})

    csv_path   = BUNDLE_DIR / config["csv_path"]
    rows       = list(csv.DictReader(open(csv_path, encoding="utf-8")))
    fieldnames = list(rows[0].keys()) if rows else []

    mode = "REPORT" if args.report else ("DRY-RUN" if args.dry_run else "LIVE")
    print(f"\n[INFO] {len(rows)} rows  |  {mode} mode\n")

    changed_rows  = 0
    changed_cells = 0
    gap_count     = 0

    for row in rows:
        wi_id   = row.get("ID (ADO)", "").strip()
        wi_type = row.get("Type",     "").strip()
        state   = row.get("State (ADO)", "").strip()
        title   = row.get("Title",    "").strip()
        current = row.get("Priority", "").strip()

        if not wi_type or not title:
            continue
        if args.ids and wi_id not in args.ids:
            continue
        if args.type and wi_type.lower() != args.type.lower():
            continue
        if not args.all and state not in OPEN_STATES:
            continue
        if current:
            continue  # already set — never overwrite

        # Determine default: type-specific first, then global fallback
        suggested = str(type_map.get(wi_type, fallback_priority))
        labels    = {1: "Critical", 2: "High", 3: "Medium", 4: "Low"}
        label     = labels.get(int(suggested), "")
        id_label  = f"#{wi_id}" if wi_id else "(new)"

        print(f"  {id_label:<8} [{wi_type:<14}]  Priority: (blank) -> {suggested} ({label})"
              f"  {title[:50]}")

        gap_count += 1
        if not args.report:
            row["Priority"] = suggested
            changed_cells  += 1
            changed_rows   += 1

    print()
    if args.report:
        print(f"  {gap_count} item(s) have no Priority set.")
    elif args.dry_run:
        print(f"  [DRY-RUN] Would set Priority on {changed_rows} item(s). No file written.")
    else:
        if changed_rows == 0:
            print("  All items already have Priority set. Nothing to do.")
        else:
            with open(csv_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            print(f"  Set Priority on {changed_rows} item(s). Run ado-sync to push to ADO.")
    print()


if __name__ == "__main__":
    main()
