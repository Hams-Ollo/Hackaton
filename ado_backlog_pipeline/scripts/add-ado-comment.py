#!/usr/bin/env python3
"""
add-ado-comment.py  (ado_backlog_pipeline bundle)
====================================================
Append a comment / history entry to one or more Azure DevOps work items,
optionally also updating state.

.env: place your credentials in ado_backlog_pipeline/.env (copy .env.example → .env).

Usage
-----
  python add-ado-comment.py --id 1234 --comment "Deployed to staging"
  python add-ado-comment.py --id 1234 --id 1235 --comment "Sprint 9 review done"
  python add-ado-comment.py --id 1234 --comment "Completed" --state Closed
  python add-ado-comment.py --id 1234 --comment "Test" --dry-run
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

SCRIPT_DIR    = Path(__file__).resolve().parent
BUNDLE_DIR    = SCRIPT_DIR.parent
WORKSPACE_DIR = BUNDLE_DIR.parent

ENV_PATH = BUNDLE_DIR / ".env"

try:
    from dotenv import load_dotenv
    load_dotenv(ENV_PATH)
except ImportError:
    pass

try:
    from azure.devops.connection import Connection
    from azure.devops.v7_1.work_item_tracking.models import JsonPatchOperation
    from msrest.authentication import BasicAuthentication
except ImportError:
    print("[ERROR] azure-devops SDK not installed. Run: pip install azure-devops msrest")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Add a comment to ADO work items")
    parser.add_argument("--id",      type=int, action="append", required=True,
                        dest="ids",  help="Work item ID (repeatable)")
    parser.add_argument("--comment", required=True, help="Comment text for System.History")
    parser.add_argument("--state",   default=None,
                        help="Also update state (e.g. Active, Closed)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print patch document without writing to ADO")
    args = parser.parse_args()

    org_url = os.environ.get("ADO_ORG_URL", "")
    project = os.environ.get("ADO_PROJECT", "")
    pat     = os.environ.get("ADO_PAT", "")

    if not pat and not args.dry_run:
        print("[ERROR] ADO_PAT not set. Add it to ado_backlog_pipeline/.env")
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    comment_html = f"{args.comment} <i>(added {timestamp})</i>"

    patch_ops = [JsonPatchOperation(op="add", path="/fields/System.History", value=comment_html)]
    if args.state:
        patch_ops.append(JsonPatchOperation(op="add", path="/fields/System.State", value=args.state))

    if args.dry_run:
        print(f"[DRY-RUN] Would patch {len(args.ids)} item(s): {args.ids}")
        for op in patch_ops:
            print(f"  {op.op}  {op.path}  =  {str(op.value)[:80]}")
        return

    credentials = BasicAuthentication("", pat)
    connection  = Connection(base_url=org_url, creds=credentials)
    wit_client  = connection.clients.get_work_item_tracking_client()

    success = 0
    for wi_id in args.ids:
        try:
            wit_client.update_work_item(document=patch_ops, id=wi_id, project=project)
            state_note = f"  -> state [{args.state}]" if args.state else ""
            print(f"  [OK]     #{wi_id}  comment added{state_note}")
            success += 1
        except Exception as exc:
            print(f"  [ERROR]  #{wi_id}  {exc}")

    print(f"\n  Done. {success}/{len(args.ids)} item(s) updated.\n")


if __name__ == "__main__":
    main()
