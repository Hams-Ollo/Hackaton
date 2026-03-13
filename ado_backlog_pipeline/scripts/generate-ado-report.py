#!/usr/bin/env python3
"""
generate-ado-report.py  (ado_backlog_pipeline bundle)
========================================================
Query Azure DevOps and generate a Markdown status report.

.env: place your credentials in ado_backlog_pipeline/.env (copy .env.example → .env).

Usage
-----
  python generate-ado-report.py                                  # last 1 day, stdout
  python generate-ado-report.py --days 7 --output report.md     # last 7 days, file
  python generate-ado-report.py --all-active                     # all active items
  python generate-ado-report.py --iteration "Hackaton\\Sprint 1"
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone

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
    from azure.devops.v7_1.work_item_tracking.models import Wiql, TeamContext
    from msrest.authentication import BasicAuthentication
except ImportError:
    print("[ERROR] azure-devops SDK not installed. Run: pip install azure-devops msrest")
    sys.exit(1)

DONE_STATES    = {"Closed", "Done", "Resolved"}
ACTIVE_STATES  = {"Active", "In Progress", "Committed"}

# Full field set — kept in sync with pull-ado-workitems.py ADO_FIELDS
FIELDS = [
    "System.Id",
    "System.WorkItemType",
    "System.Title",
    "System.State",
    "System.Reason",
    "System.AssignedTo",
    "System.IterationPath",
    "System.AreaPath",
    "System.ChangedDate",
    "System.CreatedDate",
    "System.Tags",
    "System.Parent",
    "System.CommentCount",
    "System.RelatedLinkCount",
    "System.BoardColumn",
    "System.BoardLane",
    "Microsoft.VSTS.Common.Priority",
    "Microsoft.VSTS.Common.BacklogPriority",
    "Microsoft.VSTS.Common.StateChangeDate",
    "Microsoft.VSTS.Common.ActivatedDate",
    "Microsoft.VSTS.Common.ResolvedDate",
    "Microsoft.VSTS.Common.ClosedDate",
    "Microsoft.VSTS.Common.BusinessValue",
    "Microsoft.VSTS.Common.TimeCriticality",
    "Microsoft.VSTS.Common.Risk",
    "Microsoft.VSTS.Common.Severity",
    "Microsoft.VSTS.Scheduling.StoryPoints",
    "Microsoft.VSTS.Scheduling.Effort",
    "Microsoft.VSTS.Scheduling.StartDate",
    "Microsoft.VSTS.Scheduling.TargetDate",
    "Microsoft.VSTS.CMMI.Blocked",
]


def build_wiql(project: str, days: int | None, all_active: bool, iteration: str | None) -> str:
    conditions = [f"[System.TeamProject] = '{project}'"]
    if all_active:
        conditions.append("[System.State] IN ('Active', 'In Progress', 'New', 'Committed')")
    elif days is not None:
        conditions.append(f"[System.ChangedDate] >= @Today - {days}")
    if iteration:
        conditions.append(f"[System.IterationPath] UNDER '{iteration}'")
    where = " AND ".join(conditions)
    return (
        f"SELECT {', '.join(f'[{f}]' for f in FIELDS)} "
        f"FROM workitems WHERE {where} ORDER BY [System.ChangedDate] DESC"
    )


def render_markdown(items: list[dict], args: argparse.Namespace) -> str:
    now   = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    org   = os.environ.get("ADO_ORG_URL", "https://dev.azure.com/ADM-Agentic")
    proj  = os.environ.get("ADO_PROJECT", "ADM-Agentic")
    lines = [
        "# ADO Work Item Status Report",
        f"**Generated:** {now}   **Project:** {proj}",
    ]
    if args.iteration:
        lines.append(f"**Iteration:** {args.iteration}")
    lines.append("")

    done    = [i for i in items if i["state"] in DONE_STATES]
    active  = [i for i in items if i["state"] in ACTIVE_STATES]
    other   = [i for i in items if i["state"] not in DONE_STATES | ACTIVE_STATES]

    def section(title: str, emoji: str, group: list[dict]) -> None:
        lines.append(f"## {emoji} {title} ({len(group)})")
        if not group:
            lines.append("_No items._\n"); return
        lines.append("| ID | Type | Title | State | P | Pts | Risk/Sev | Blocked | Board Column | State Changed | Iteration |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
        for item in group:
            url   = f"{org}/{proj}/_workitems/edit/{item['id']}"
            t     = item["title"].replace("|", "\\|")[:50]
            pts   = item.get("points", "") or ""
            prio  = item.get("priority", "") or ""
            risk  = item.get("risk", "") or item.get("severity", "") or ""
            blk   = item.get("blocked", "") or ""
            bcol  = item.get("board_column", "") or ""
            sc    = item.get("state_changed", "") or ""
            lines.append(
                f"| [#{item['id']}]({url}) | {item['type']} | {t} "
                f"| {item['state']} | {prio} | {pts} | {risk} | {blk} "
                f"| {bcol} | {sc} "
                f"| {item['iteration'].split(chr(92))[-1]} |"
            )
        lines.append("")

    section("Done / Closed",       "✅", done)
    section("Active / In Progress","🔄", active)
    section("New / Other",         "⏳", other)
    lines += ["---", f"_Total items: {len(items)}_"]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate ADO work item status report")
    parser.add_argument("--days",       type=int, default=1)
    parser.add_argument("--all-active", action="store_true")
    parser.add_argument("--iteration",  default=None)
    parser.add_argument("--output",     default=None)
    args = parser.parse_args()

    org_url = os.environ.get("ADO_ORG_URL", "https://dev.azure.com/ADM-Agentic")
    project = os.environ.get("ADO_PROJECT", "ADM-Agentic")
    pat     = os.environ.get("ADO_PAT", "")

    if not pat:
        print("[ERROR] ADO_PAT not set."); sys.exit(1)

    credentials  = BasicAuthentication("", pat)
    connection   = Connection(base_url=org_url, creds=credentials)
    wit_client   = connection.clients.get_work_item_tracking_client()

    wiql_str     = build_wiql(project, args.days if not args.all_active else None,
                               args.all_active, args.iteration)
    team_context = TeamContext(project=project)
    result       = wit_client.query_by_wiql(Wiql(query=wiql_str), team_context=team_context)
    wi_refs      = result.work_items or []

    if not wi_refs:
        print("[INFO] No work items matched."); return

    batch = wit_client.get_work_items(ids=[r.id for r in wi_refs], fields=FIELDS)

    items = []
    for wi in batch:
        f = wi.fields or {}
        ar = f.get("System.AssignedTo", "")
        items.append({
            "id":               wi.id,
            "type":             f.get("System.WorkItemType", ""),
            "title":            f.get("System.Title", ""),
            "state":            f.get("System.State", ""),
            "reason":           f.get("System.Reason", ""),
            "assignee":         ar.get("displayName", str(ar)) if isinstance(ar, dict) else str(ar),
            "iteration":        f.get("System.IterationPath", ""),
            "area_path":        f.get("System.AreaPath", ""),
            "priority":         f.get("Microsoft.VSTS.Common.Priority", ""),
            "backlog_priority": f.get("Microsoft.VSTS.Common.BacklogPriority", ""),
            "points":           f.get("Microsoft.VSTS.Scheduling.StoryPoints",
                                      f.get("Microsoft.VSTS.Scheduling.Effort", "")),
            "business_value":   f.get("Microsoft.VSTS.Common.BusinessValue", ""),
            "time_criticality": f.get("Microsoft.VSTS.Common.TimeCriticality", ""),
            "risk":             f.get("Microsoft.VSTS.Common.Risk", ""),
            "severity":         f.get("Microsoft.VSTS.Common.Severity", ""),
            "blocked":          f.get("Microsoft.VSTS.CMMI.Blocked", ""),
            "board_column":     f.get("System.BoardColumn", ""),
            "board_lane":       f.get("System.BoardLane", ""),
            "comment_count":    f.get("System.CommentCount", ""),
            "related_links":    f.get("System.RelatedLinkCount", ""),
            "created_date":     str(f.get("System.CreatedDate", "") or "")[:10],
            "changed_date":     str(f.get("System.ChangedDate", "") or "")[:10],
            "state_changed":    str(f.get("Microsoft.VSTS.Common.StateChangeDate", "") or "")[:10],
            "activated_date":   str(f.get("Microsoft.VSTS.Common.ActivatedDate", "") or "")[:10],
            "resolved_date":    str(f.get("Microsoft.VSTS.Common.ResolvedDate", "") or "")[:10],
            "closed_date":      str(f.get("Microsoft.VSTS.Common.ClosedDate", "") or "")[:10],
            "start_date":       str(f.get("Microsoft.VSTS.Scheduling.StartDate", "") or "")[:10],
            "target_date":      str(f.get("Microsoft.VSTS.Scheduling.TargetDate", "") or "")[:10],
            "tags":             f.get("System.Tags", "") or "",
        })

    report = render_markdown(items, args)

    if args.output:
        out = Path(args.output)
        out.write_text(report, encoding="utf-8")
        print(f"[INFO] Report saved -> {out.resolve()}")
    else:
        print("\n" + report)


if __name__ == "__main__":
    main()
