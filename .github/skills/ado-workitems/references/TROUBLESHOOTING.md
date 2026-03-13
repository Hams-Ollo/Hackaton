# ADO Work Item Skill Troubleshooting

## Common Failures

### No items found

The local CSV may be empty or filtered too narrowly. Run a pull first.

### Row changes did not sync

Verify `_row_dirty=1`. The sync script ignores rows without that flag.

### Assigned To failed

The display name likely does not match a configured value in `ado-config.yaml`.

### Iteration path failed

The shorthand in `Iteration #` likely does not exist in `iteration_map`.

### Description contains HTML entities

This is expected when data originated in ADO. The pull script normalizes and decodes content.

### Schema mismatch

Run `python ado_backlog_pipeline/scripts/migrate-csv-schema.py --dry-run` and inspect the proposed changes.

## Recovery Pattern

1. Pull the latest ADO state.
2. Recheck the target row.
3. Reapply the minimal required edits.
4. Set `_row_dirty=1`.
5. Run sync again.
