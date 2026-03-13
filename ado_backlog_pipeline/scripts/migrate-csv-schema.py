"""
migrate-csv-schema.py
One-time migration: upgrades an existing work-log CSV from the legacy 27-column
schema to the new 43-column canonical schema.

Usage:
    python scripts/migrate-csv-schema.py [--csv-path PATH] [--dry-run]

Options:
    --csv-path PATH  Path to the CSV to migrate.
                     Defaults to data/work-log.csv relative to the
                     ado_backlog_pipeline/ directory.
    --dry-run        Print what would change without writing any files.
"""

import argparse
import csv
import shutil
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Canonical 43-column schema (in order)
# ---------------------------------------------------------------------------
CANONICAL_FIELDNAMES: list[str] = [
    "ID (ADO)",
    "Type",
    "Parent ID (ADO)",
    "Title",
    "Area Path",
    "Iteration #",
    "Priority",
    "Backlog Priority",
    "Story Points",
    "Effort",
    "Business Value",
    "Time Criticality",
    "Risk",
    "Severity",
    "Start (MM/DD/YYYY)",
    "End (MM/DD/YYYY)",
    "State (ADO)",
    "Reason",
    "Blocked",
    "Board Column",
    "Board Lane",
    "Created Date (ADO)",
    "Changed Date (ADO)",
    "State Changed Date (ADO)",
    "Activated Date (ADO)",
    "Resolved Date (ADO)",
    "Closed Date (ADO)",
    "Assigned To (ADO)",
    "Tags",
    "Comment Count",
    "Related Link Count",
    "Description",
    "Status",
    "Owner",
    "Dev Lead",
    "Work Notes",
    "Comments",
    "Blocker/Dependency",
    "Branch Name",
    "Branch Repo",
    "In scope for DEMO or MVP Release?",
    "Last Synced (ADO)",
    "_row_dirty",
]

# ---------------------------------------------------------------------------
# Legacy → canonical column renames
# Map any old column names that changed to their new equivalents.
# Columns whose names didn't change don't need an entry here.
# ---------------------------------------------------------------------------
RENAME_MAP: dict[str, str] = {
    # old name → new name
    "Iteration": "Iteration #",
    "Start Date": "Start (MM/DD/YYYY)",
    "End Date": "End (MM/DD/YYYY)",
    "Target Date": "End (MM/DD/YYYY)",
    "Assigned To": "Assigned To (ADO)",
    "Created Date": "Created Date (ADO)",
    "Changed Date": "Changed Date (ADO)",
    "State Changed Date": "State Changed Date (ADO)",
    "Activated Date": "Activated Date (ADO)",
    "Resolved Date": "Resolved Date (ADO)",
    "Closed Date": "Closed Date (ADO)",
    "Last Synced": "Last Synced (ADO)",
    "Parent": "Parent ID (ADO)",
    "ID": "ID (ADO)",
    "State": "State (ADO)",
}


def _resolve_default_csv() -> Path:
    """Return the default CSV path: data/work-log.csv under ado_backlog_pipeline/."""
    here = Path(__file__).resolve().parent          # scripts/
    return here.parent / "data" / "work-log.csv"    # data/work-log.csv


def migrate(csv_path: Path, dry_run: bool) -> None:
    if not csv_path.exists():
        print(f"ERROR: CSV not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    # ---- read -------------------------------------------------------
    with csv_path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        old_fieldnames: list[str] = list(reader.fieldnames or [])
        rows: list[dict[str, str]] = list(reader)

    print(f"Input : {csv_path}")
    print(f"Rows  : {len(rows)}")
    print(f"Old columns ({len(old_fieldnames)}): {old_fieldnames}")

    # ---- apply rename map to every row ------------------------------
    renamed_rows: list[dict[str, str]] = []
    for row in rows:
        new_row: dict[str, str] = {}
        for k, v in row.items():
            canonical_key = RENAME_MAP.get(k, k)
            # If multiple old columns map to the same new column keep first non-empty
            if canonical_key in new_row and not new_row[canonical_key]:
                new_row[canonical_key] = v
            elif canonical_key not in new_row:
                new_row[canonical_key] = v
        renamed_rows.append(new_row)

    # ---- figure out what's new / dropped ----------------------------
    old_mapped = {RENAME_MAP.get(c, c) for c in old_fieldnames}
    new_cols = [c for c in CANONICAL_FIELDNAMES if c not in old_mapped]
    dropped_cols = [c for c in old_mapped if c not in CANONICAL_FIELDNAMES]

    print(f"\nNew columns to add   ({len(new_cols)}): {new_cols}")
    if dropped_cols:
        print(f"Legacy cols not kept ({len(dropped_cols)}): {dropped_cols}")
        print("  (Their values will still be preserved under the new names "
              "or silently dropped if they have no mapping.)")

    # ---- build output rows in canonical column order ----------------
    output_rows: list[dict[str, str]] = []
    for row in renamed_rows:
        out: dict[str, str] = {col: row.get(col, "") for col in CANONICAL_FIELDNAMES}
        output_rows.append(out)

    # ---- dry-run: just report ---------------------------------------
    if dry_run:
        print("\n[DRY RUN] No files written.")
        print(f"  Would back up   : {csv_path} → {csv_path}.bak")
        print(f"  Would write     : {len(output_rows)} rows × {len(CANONICAL_FIELDNAMES)} columns")
        return

    # ---- backup original --------------------------------------------
    backup_path = csv_path.with_suffix(csv_path.suffix + ".bak")
    shutil.copy2(csv_path, backup_path)
    print(f"\nBackup  : {backup_path}")

    # ---- write migrated file ----------------------------------------
    with csv_path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=CANONICAL_FIELDNAMES)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Written : {csv_path}")
    print(f"\nMigration complete: {len(output_rows)} rows, "
          f"{len(new_cols)} new columns added, "
          f"{len(CANONICAL_FIELDNAMES)} total columns.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Migrate work-log CSV from legacy schema to 43-column canonical schema."
    )
    parser.add_argument(
        "--csv-path",
        type=Path,
        default=None,
        help="Path to the CSV file to migrate (default: data/work-log.csv)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing any files.",
    )
    args = parser.parse_args()

    csv_path: Path = args.csv_path if args.csv_path else _resolve_default_csv()
    migrate(csv_path.resolve(), dry_run=args.dry_run)


if __name__ == "__main__":
    main()
