---
name: github-issues
description: Manage GitHub Issues — create, update, close, label, assign, and comment. Use when the user asks to create a bug, feature, task, or epic; update issue state, labels, or assignees; close resolved issues; or add work notes as comments. Targets Terraformers-Anonymous/hackathon-project via the GitHub MCP server.
argument-hint: "[new | update <#> | close <#> | comment <#> | label <#> | assign <#>]"
---

# GitHub Issues Management Skill

Use this skill for all GitHub Issues operations. Execution is via the `github` MCP server configured in `.vscode/mcp.json`. Configuration lives in `github_devflow/config/github-config.yaml`.

## When To Use This Skill

- Create a new GitHub Issue (bug, feature, task, epic, user story)
- Update an existing issue (title, body, state, labels, assignees, milestone)
- Close or reopen an issue
- Add a comment to an issue (work notes, status updates)
- Apply or remove labels
- Assign or reassign team members

## Operational Boundaries

- All GitHub usernames come from `assignee_map` in `github_devflow/config/github-config.yaml`.
- All label names come from `issue_type_labels`, `priority_labels`, and `auto_labels` in the same config.
- Auto-labels (`hackathon`, `agentic-devops`) are applied to every created issue — never omit them.
- After creating an issue, always add it to the project board (use `github-projects` skill or call directly).
- Never close an issue without confirming the linked PR is merged or work is verified done.
- Assignees and labels are issue-level — they cannot be set via the Projects v2 API.

## Standard Execution Flow

### New Issue
1. Resolve assignee GitHub username from `assignee_map`.
2. Build labels array: type label + priority label + `auto_labels`.
3. Call `create_issue` with title, body, labels, and assignee.
4. Add issue to project board and set Status = "Todo" (see `github-projects` skill).

### Update Issue
1. Call `update_issue` with only the changed fields.
2. If status changed semantically, update the project board Status field too.

### Comment / Work Notes
1. Draft comment in professional past tense with specific deliverables.
2. Call `add_issue_comment`.

## Reference Material

- [references/REFERENCE.md](references/REFERENCE.md) — field rules, label taxonomy, MCP tool names
- [references/WORKFLOWS.md](references/WORKFLOWS.md) — step-by-step procedures
- [references/TROUBLESHOOTING.md](references/TROUBLESHOOTING.md) — common failures and recovery

## Output Rules

- Always confirm with issue number and URL after creation or update.
- For bulk operations, show a table of proposed changes before executing.
- Work notes / comments must be professional and in past tense.
