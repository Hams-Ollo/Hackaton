# GitHub Projects Skill Reference

## Runtime Layout

- Skill entrypoint: `.github/skills/github-projects/SKILL.md`
- Config: `github_devflow/config/github-config.yaml`
- MCP server: `github` `projects` toolset (configured in `.vscode/mcp.json`)
- API type: GraphQL (not REST)
- Fixed org: `Terraformers-Anonymous`
- Fixed project number: `1`

## MCP Operations (github server, projects toolset)

| Operation | GraphQL Mutation / Query | Returns |
|---|---|---|
| Add issue/PR to board | `addProjectV2ItemById(projectId, contentId)` | `itemId` (PVTI_...) |
| Update single-select field | `updateProjectV2ItemFieldValue` with `singleSelectOptionId` | updated item |
| Update iteration field | `updateProjectV2ItemFieldValue` with `iterationId` | updated item |
| Update text/number field | `updateProjectV2ItemFieldValue` with `text` or `number` | updated item |
| Remove item from board | `deleteProjectV2Item(projectId, itemId)` | does NOT close the issue |
| List project items | projects query | all items with field values |
| List project fields | projects query | field IDs, option IDs, iteration IDs |

## Node ID Formats

| Entity | Format | Example |
|---|---|---|
| Project node ID | `PVT_...` | `PVT_kwDOBxyz` |
| Issue node ID | `I_kgDO...` | `I_kgDOABCD` |
| PR node ID | `PR_kgDO...` | `PR_kgDOEFGH` |
| Project item node ID | `PVTI_...` | `PVTI_lADOXYZ` |
| Single-select option ID | `PVTSSF_...` | `PVTSSF_kgDO` |
| Iteration ID | `iteration:...` | varies per project |

## Field Types

| Field | GraphQL Type | How to Set |
|---|---|---|
| Status | `ProjectV2SingleSelectField` | `value: { singleSelectOptionId: "..." }` |
| Priority | `ProjectV2SingleSelectField` | `value: { singleSelectOptionId: "..." }` |
| Sprint | `ProjectV2IterationField` | `value: { iterationId: "..." }` |
| Text (custom) | `ProjectV2Field` | `value: { text: "..." }` |
| Number (custom) | `ProjectV2Field` | `value: { number: N }` |
| Date (custom) | `ProjectV2Field` | `value: { date: "YYYY-MM-DD" }` |

## Critical Constraints

- **Cannot add and update in the same call** — always two separate calls: add first, then update field.
- **Assignees and Labels** are on the underlying Issue, NOT on the project item. Use `github-issues` skill for those.
- **Status option IDs** are GraphQL node IDs unique to this project — store in config, never hardcode in prompts.
- **Iteration IDs** change each sprint — always query dynamically from the `ProjectV2IterationField`.
- **projectId** is needed for every project mutation — cache in `project_fields.project_id` in config.
- **itemId** (returned by `addProjectV2ItemById`) is required for field updates — not the same as the issue node_id.

## First-Time Setup: Query Field IDs

Ask Copilot: *"List all fields on project 1 for org Terraformers-Anonymous using the github MCP server"*

Expected output includes:
- `projectId` (PVT_...) → put in `project_fields.project_id`
- Status field ID → put in `project_fields.status.field_id`
- Status option IDs for Todo/In Progress/Done → put in `project_fields.status.options`
- Priority field ID and option IDs → put in `project_fields.priority`
- Sprint field ID → put in `project_fields.sprint.field_id`
