# GitHub Projects Skill Troubleshooting

## Common Failures

### project_id is empty in config
Query the project node ID: ask Copilot "get project 1 for org Terraformers-Anonymous" via the github MCP server.
The GraphQL node ID starts with `PVT_...`. Update `project_fields.project_id` in `github_devflow/config/github-config.yaml` and commit.

### Field update returns error — field_id is empty or wrong
Re-query all field IDs: ask Copilot "list all fields on project 1 for Terraformers-Anonymous".
Update `project_fields.status.field_id`, `project_fields.priority.field_id`, and `project_fields.sprint.field_id` in config.

### singleSelectOptionId is invalid or stale
Option IDs are stable but can change if the field is deleted and recreated.
Re-query the Status or Priority field options and update the `options` map in config.

### iterationId not found
Iteration IDs change each sprint. You cannot hardcode them.
Always query the `ProjectV2IterationField` dynamically to get the current sprint's `iterationId`.

### Field update fails — wrong itemId
The `itemId` (PVTI_...) is the project item's node ID, returned by `addProjectV2ItemById`.
It is different from the issue's `node_id` (I_kgDO...).
Query project items to get the correct `itemId` for the target issue.

### Item added to board but fields are blank
Field updates require a separate call after `addProjectV2ItemById`.
Ensure you used the `itemId` returned by the add operation, not the `contentId`.
Then call `updateProjectV2ItemFieldValue` for each field.

### deleteProjectV2Item closed the issue
`deleteProjectV2Item` only removes the item from the project board — it does NOT close the issue.
To close the issue, call `update_issue` with `state: closed` separately.

### Assignees not updating via project API
Assignees are a property of the underlying GitHub Issue, not the project item.
Use `update_issue` (assignees field) via the `github-issues` skill instead.

## Recovery Pattern

1. Query the project to list all items — get current `itemId` values.
2. Query all project fields — get fresh `fieldId`, option IDs, and iteration IDs.
3. Update `github_devflow/config/github-config.yaml` with the correct values.
4. Retry the field update using the correct `projectId`, `itemId`, and `fieldId`.
