# ADO Work Item Skill Reference

This reference contains the durable rules behind the `ado-workitems` skill.

## Runtime Layout

- Skill entrypoint: `.github/skills/ado-workitems/SKILL.md`
- Operational bundle: `ado_backlog_pipeline/`
- Scripts: `ado_backlog_pipeline/scripts/`
- Config: `ado_backlog_pipeline/config/ado-config.yaml`
- Canonical CSV: `ado_backlog_pipeline/data/ado_azure_ai_search_work_items.csv`
- Planning scratchpad: `ado_backlog_pipeline/data/TODO.md`
- Session notes: `ado_backlog_pipeline/data/WORK_NOTES.md`

## Source Of Truth Hierarchy

All ADO board state flows through three local files. Keep them aligned.

| File | Role |
|---|---|
| `ado_backlog_pipeline/data/ado_azure_ai_search_work_items.csv` | Master record for ADO create and update pushes |
| `ado_backlog_pipeline/data/TODO.md` | Sprint planning list and creation candidates |
| `ado_backlog_pipeline/data/WORK_NOTES.md` | Session log used to draft Work Notes for ADO |

## Canonical Sync Rules

1. `TODO.md` items in the active sprint without an `ADO#ID` are candidates for new CSV rows.
2. The CSV is the push gate. Any row that must be pushed needs `_row_dirty=1`.
3. `WORK_NOTES.md` notes tagged with `**ADO#ID**` should be copied into the row `Work Notes` column before sync.
4. After sync creates a new item, write the generated `ADO#ID` back into the matching `TODO.md` line.
5. After pull, move items that are resolved, done, or closed into the `TODO.md` done section when appropriate.

## Read-Only Fields

Never write these fields directly:

- `Backlog Priority`
- `Reason`
- `Board Column`
- `Board Lane`
- `Created Date (ADO)`
- `Changed Date (ADO)`
- `State Changed Date (ADO)`
- `Activated Date (ADO)`
- `Resolved Date (ADO)`
- `Closed Date (ADO)`
- `Comment Count`
- `Related Link Count`
- `Last Synced (ADO)`

## Field Rules

- Leave `ID (ADO)` blank for new rows.
- Use `Effort` for Epic and Feature work items.
- Use `Story Points` for User Story and Task work items.
- Use `Risk` only for Epic, Feature, and User Story work items.
- Use `Severity` only for Bug work items.
- Use `Blocked` only for Bug and Task work items.
- Use shorthand values in `Iteration #` that exist in `iteration_map`.

## Script Commands

- Pull: `python ado_backlog_pipeline/scripts/pull-ado-workitems.py`
- Sync: `python ado_backlog_pipeline/scripts/sync-ado-workitems.py`
- Report: `python ado_backlog_pipeline/scripts/generate-ado-report.py`
- Migrate: `python ado_backlog_pipeline/scripts/migrate-csv-schema.py --dry-run`
- Add comment: `python ado_backlog_pipeline/scripts/add-ado-comment.py`

## Pre-Flight Checks

Run these before invoking a script:

```powershell
python --version
Test-Path ado_backlog_pipeline/.env
```
