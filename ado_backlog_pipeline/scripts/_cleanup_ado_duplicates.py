#!/usr/bin/env python3
"""
_cleanup_ado_duplicates.py
--------------------------
Deletes ADO work items accidentally created by sync-ado-workitems.py
when the CSV had a UTF-8 BOM that caused all IDs to appear blank.

Queries for items with ID > MAX_LEGIT_ID created today, lists them,
then deletes them.

Usage:
    uv run python ado_backlog_pipeline/scripts/_cleanup_ado_duplicates.py --dry-run
    uv run python ado_backlog_pipeline/scripts/_cleanup_ado_duplicates.py
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import date

# The highest legitimately-existing item ID before the accidental sync
MAX_LEGIT_ID = 1643

SCRIPT_DIR  = Path(__file__).resolve().parent
BUNDLE_DIR  = SCRIPT_DIR.parent
ENV_PATH    = BUNDLE_DIR / ".env"
CONFIG_PATH = BUNDLE_DIR / "config" / "ado-config.yaml"

try:
    from dotenv import load_dotenv
    load_dotenv(ENV_PATH)
except ImportError:
    pass

try:
    import yaml
except ImportError:
    print("[ERROR] PyYAML not installed. Run: uv add pyyaml")
    sys.exit(1)

try:
    from azure.devops.connection import Connection
    from azure.devops.v7_1.work_item_tracking.models import Wiql, TeamContext
    from msrest.authentication import BasicAuthentication
except ImportError:
    print("[ERROR] azure-devops SDK not installed. Run: uv add azure-devops msrest")
    sys.exit(1)

# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser(description="Delete accidental duplicate ADO items.")
parser.add_argument("--dry-run", action="store_true", help="List items only, do not delete.")
parser.add_argument("--max-legit-id", type=int, default=MAX_LEGIT_ID,
                    help=f"Highest legitimate item ID (default: {MAX_LEGIT_ID})")
args = parser.parse_args()

cfg     = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
PAT     = os.environ.get("ADO_PAT", "")
ORG_URL = cfg["ado"]["org_url"]
PROJECT = cfg["ado"]["project"]

if not PAT:
    print("[ERROR] ADO_PAT not set. Check ado_backlog_pipeline/.env")
    sys.exit(1)

connection = Connection(base_url=ORG_URL, creds=BasicAuthentication("", PAT))
wit_client = connection.clients.get_work_item_tracking_client()

today_str = date.today().isoformat()
print(f"[INFO] Querying for items with ID > {args.max_legit_id} created on {today_str}...")

wiql_str = (
    f"SELECT [System.Id], [System.Title], [System.WorkItemType], [System.CreatedDate] "
    f"FROM WorkItems "
    f"WHERE [System.TeamProject] = '{PROJECT}' "
    f"  AND [System.Id] > {args.max_legit_id} "
    f"  AND [System.CreatedDate] >= '{today_str}T00:00:00Z' "
    f"ORDER BY [System.Id] ASC"
)

team_context = TeamContext(project=PROJECT)
result = wit_client.query_by_wiql(Wiql(query=wiql_str), team_context=team_context)
ids = [r.id for r in (result.work_items or [])]

if not ids:
    print("[INFO] No duplicate items found. Nothing to delete.")
    sys.exit(0)

print(f"[INFO] Found {len(ids)} duplicate item(s): #{ids[0]} – #{ids[-1]}")

# Fetch titles in batches of 200
info_items = []
for start in range(0, len(ids), 200):
    chunk = ids[start : start + 200]
    details = wit_client.get_work_items(
        ids=chunk,
        fields=["System.Id", "System.Title", "System.WorkItemType"],
        error_policy="omit",
    )
    info_items.extend(wi for wi in (details or []) if wi is not None)

print(f"\nItems to be {'listed (dry-run)' if args.dry_run else 'DELETED'}:")
for wi in info_items[:30]:
    t = wi.fields.get("System.WorkItemType", "?")
    title = wi.fields.get("System.Title", "")[:60]
    print(f"  #{wi.id:<6}  [{t:<12}]  {title}")
if len(info_items) > 30:
    print(f"  ... and {len(info_items) - 30} more")

if args.dry_run:
    print(f"\n[DRY-RUN] Would delete {len(ids)} items. Re-run without --dry-run to proceed.")
    sys.exit(0)

# Confirm before deleting
confirm = input(f"\nProceed with deleting {len(ids)} items? Type 'yes' to confirm: ").strip().lower()
if confirm != "yes":
    print("Aborted — no items deleted.")
    sys.exit(0)

deleted = errors = 0
for wi_id in ids:
    try:
        wit_client.delete_work_item(id=wi_id, project=PROJECT, destroy=False)
        print(f"  [DELETED] #{wi_id}")
        deleted += 1
    except Exception as e:
        print(f"  [ERROR]   #{wi_id} -> {e}")
        errors += 1

print(f"\n[DONE] Deleted: {deleted}  Errors: {errors}")
