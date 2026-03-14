# GitHub Issues Skill Troubleshooting

## Common Failures

### Label not found
The label does not exist in the repo. Use `list_labels` to see available labels.
Create missing labels via the GitHub UI (Settings → Labels) or ask Copilot to create them using the `labels` MCP toolset.
Then retry the issue creation or update.

### Assignee rejected / not added
The GitHub username is not a member of the org or does not have repo access.
- Check `assignee_map` in `github_devflow/config/github-config.yaml` for correct username spelling.
- Verify the user has accepted their org invitation and has at least read access to the repo.

### Issue created but not on project board
`create_issue` succeeded but `addProjectV2ItemById` was not called, or the project `project_id` in config is empty.
- Get the issue's `node_id` from the `create_issue` response.
- Query the project node ID: ask Copilot "get project 1 for org Terraformers-Anonymous" — the ID starts with `PVT_...`.
- Update `project_fields.project_id` in `github_devflow/config/github-config.yaml`.
- Call `addProjectV2ItemById` with the correct `projectId` and `contentId`.

### project_fields IDs are empty in config
Run: ask Copilot "list all fields on project 1 for org Terraformers-Anonymous" using the GitHub MCP server.
The server returns all field names, IDs, and option IDs.
Copy the values into `github_devflow/config/github-config.yaml` under `project_fields`.
Commit the updated config so the whole team benefits.

### Auto-labels missing from created issue
The `auto_labels` were not included in the labels array.
Update via `update_issue` with labels = existing labels + `hackathon` + `agentic-devops`.

### node_id not captured after create_issue
The `node_id` is needed for adding the issue to the project board.
Retrieve it by calling `get_issue` with the issue number — it is returned in the response.

## Recovery Pattern

1. Verify the issue exists and get its `number` and `node_id` via `get_issue`.
2. Verify the project exists and get `project_id` via project query.
3. Check that required labels exist via `list_labels`.
4. Update `github_devflow/config/github-config.yaml` with any missing IDs.
5. Retry the failed operation.
