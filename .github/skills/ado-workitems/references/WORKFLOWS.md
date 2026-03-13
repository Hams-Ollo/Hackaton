# ADO Work Item Skill Workflows

## New Work Item Workflow

Use when the user asks to add a task, bug, story, or other new ADO item.

1. Read the active sprint section in `ado_backlog_pipeline/data/TODO.md` and identify items without an `ADO#ID`.
2. Infer or ask for the minimum missing fields: work item type, title, summary, parent, iteration, assignee, and priority.
3. Draft the row in the canonical CSV.
4. Leave read-only fields blank.
5. Set `_row_dirty=1`.
6. Run sync if the user wants the item created in ADO.
7. After the script writes the new ID back, update the matching `TODO.md` line to include `ADO#<ID>`.

## Existing Work Item Update Workflow

Use when the user wants to log work, adjust a state, add notes, or change planning fields.

1. Locate the row by `ID (ADO)`.
2. Read `WORK_NOTES.md` for any matching `**ADO#ID**` notes before asking for more detail.
3. Draft only the fields that change.
4. Always set `_row_dirty=1`.
5. Generate Work Notes in professional past tense with specific deliverables and a `Ref:` line.
6. Copy the Work Notes into the CSV row.
7. If the item is being completed, reconcile `TODO.md` as part of the update.

## Pull And Reconcile Workflow

Use when the user asks to refresh, pull, or reconcile local backlog state.

1. Confirm `.env` exists and the environment is active.
2. Run `python ado_backlog_pipeline/scripts/pull-ado-workitems.py`.
3. Review state changes in the CSV.
4. Move resolved or closed items in `TODO.md` into the done section.
5. Ensure any new item IDs already present in the CSV are reflected in `TODO.md`.

## Diagnose Workflow

Use when sync fails or state looks wrong.

1. Check whether the CSV has rows.
2. Check whether the intended row has `_row_dirty=1`.
3. Validate assignee names against `assignee_map`.
4. Validate iteration shorthand against `iteration_map`.
5. Run schema migration in dry-run mode if the CSV shape looks outdated.
