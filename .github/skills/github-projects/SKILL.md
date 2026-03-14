---
name: github-projects
description: Manage GitHub Projects v2 board — add items, update Status, Priority, and Sprint fields, query board state, and report sprint progress. Use when the user asks about the project board, sprint status, moving cards between columns, or updating project field values for issues and PRs.
argument-hint: "[add <#> | status <#> <value> | sprint <#> <value> | report | list]"
---

# GitHub Projects v2 Management Skill

Use this skill for GitHub Projects v2 board operations. All board mutations use the GraphQL API via the `github` MCP server `projects` toolset. Configuration and field IDs live in `github_devflow/config/github-config.yaml`.

## When To Use This Skill

- Add an issue or PR to the project board
- Update the Status field (Todo / In Progress / Done)
- Update the Priority field (Critical / High / Medium / Low)
- Update the Sprint / Iteration field
- Query board state, list items by status or sprint
- Generate a sprint progress report

## Operational Boundaries

- All field IDs and option IDs come from `github_devflow/config/github-config.yaml` under `project_fields`.
- If field IDs are blank in config, query the project first and update config before writing.
- Assignees and labels are properties of the underlying issue — set those via `github-issues` skill.
- Status, Priority, and Sprint are project-level fields — only settable via GraphQL project mutations.
- Adding an item and updating its fields **always requires two separate MCP calls** — add first, then update.
- The `itemId` (project item node ID, format: `PVTI_...`) is different from the issue `node_id` — use the correct one.

## Standard Execution Flow

### Add Item to Board
1. Get issue/PR node ID via `get_issue` or `get_pull_request` (format: `I_kgDO...` or `PR_kgDO...`).
2. Get `project_id` from config (format: `PVT_...`).
3. Call `addProjectV2ItemById(projectId, contentId: node_id)` → capture `itemId`.
4. Call `updateProjectV2ItemFieldValue` to set Status = "Todo" using `singleSelectOptionId` from config.

### Update Field Value
1. Read `project_fields` in config for the correct `field_id` and `options` map.
2. For single-select (Status / Priority): use `singleSelectOptionId` from config.
3. For iteration (Sprint): query the `ProjectV2IterationField` to get current `iterationId`, then update.

### Sprint Report
1. Query all project items with their field values via `projects` toolset.
2. Group by Status field value.
3. Report: Total | Todo | In Progress | Done, with issue numbers, titles, and assignees.

## Reference Material

- [references/REFERENCE.md](references/REFERENCE.md) — GraphQL types, field constraints, tool names
- [references/WORKFLOWS.md](references/WORKFLOWS.md) — step-by-step procedures
- [references/TROUBLESHOOTING.md](references/TROUBLESHOOTING.md) — common failures and recovery

## Output Rules

- Always confirm field update with the item's issue number/title and new field value.
- For sprint reports, use a table: Issue # | Title | Status | Assignee | Priority.
