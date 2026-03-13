---
name: ado-workitems
description: Manage Azure DevOps work items via the local CSV backlog. Use when the user asks to create, update, review, push, pull, or sync ADO work items, sprints, board state, or the work-log CSV. Covers new item creation, status updates, Work Notes authoring, and running pull/sync/report scripts.
argument-hint: "[new | update <ID> | pull | sync | report | migrate]"
---

# ADO Work Item Management Skill

Use this skill for Azure DevOps work item operations that flow through the local CSV backlog pipeline. This skill is the workflow contract. The implementation lives in `ado_backlog_pipeline/` at the repo root and should stay separate from the skill directory.

## When To Use This Skill

Use this skill when the user asks to:

- create or draft a new ADO work item
- update an existing ADO work item or add professional work notes
- pull, sync, report, or migrate the ADO CSV backlog
- reconcile `TODO.md`, `WORK_NOTES.md`, and the canonical CSV
- diagnose sync failures, schema drift, or missing ADO state

## Operational Boundaries

- Treat `ado_backlog_pipeline/data/backlog.csv` as the push gate for ADO changes.
- Treat `ado_backlog_pipeline/data/TODO.md` as the planning source and `ado_backlog_pipeline/data/WORK_NOTES.md` as the session source.
- Never patch read-only ADO fields.
- Keep new team members, iterations, defaults, and mappings in `ado_backlog_pipeline/config/ado-config.yaml` rather than hardcoding behavior.
- Run scripts from the repository root so relative paths resolve correctly.

## Standard Execution Flow

1. Identify whether the user is creating, updating, syncing, reporting, or diagnosing.
2. Read the relevant local sources before drafting changes:
   - `ado_backlog_pipeline/data/TODO.md`
   - `ado_backlog_pipeline/data/WORK_NOTES.md`
   - `ado_backlog_pipeline/data/ado_azure_ai_search_work_items.csv`
3. Make the smallest required local changes first.
4. Set `_row_dirty=1` for any row that must be pushed.
5. If the user wants the change applied to ADO, run the appropriate script.
6. Reconcile `TODO.md` after pull or successful creation so every tracked item has an `ADO#ID`.

## Script Entry Points

- Pull: `python ado_backlog_pipeline/scripts/pull-ado-workitems.py`
- Sync: `python ado_backlog_pipeline/scripts/sync-ado-workitems.py`
- Report: `python ado_backlog_pipeline/scripts/generate-ado-report.py`
- Migrate: `python ado_backlog_pipeline/scripts/migrate-csv-schema.py --dry-run`
- Comment: `python ado_backlog_pipeline/scripts/add-ado-comment.py`

Before running a script, confirm the virtual environment is active and `ado_backlog_pipeline/.env` exists.

## Reference Material

- Detailed reference: [references/REFERENCE.md](references/REFERENCE.md)
- Workflow procedures: [references/WORKFLOWS.md](references/WORKFLOWS.md)
- Troubleshooting guide: [references/TROUBLESHOOTING.md](references/TROUBLESHOOTING.md)

## Output Rules

- For updates, emit only changed fields in `Column: Value` form unless the user explicitly asks for a full row.
- Work Notes must be specific, professional, and in past tense.
- If a script is needed to complete the request, state the command and run it when allowed.
