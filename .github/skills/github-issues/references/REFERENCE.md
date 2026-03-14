# GitHub Issues Skill Reference

## Runtime Layout

- Skill entrypoint: `.github/skills/github-issues/SKILL.md`
- Config: `github_devflow/config/github-config.yaml`
- MCP server: `github` (configured in `.vscode/mcp.json`)
- Fixed owner: `Terraformers-Anonymous`
- Fixed repo: `hackathon-project`

## MCP Tool Names (github server, issues toolset)

| Operation | Tool Name | Key Parameters |
|---|---|---|
| Get issue | `get_issue` | `owner`, `repo`, `issue_number` |
| List issues | `list_issues` | `owner`, `repo`, `state`, `labels`, `assignee` |
| Create issue | `create_issue` | `owner`, `repo`, `title`, `body`, `labels[]`, `assignees[]` |
| Update issue | `update_issue` | `owner`, `repo`, `issue_number`, `state`, `labels[]`, `assignees[]`, `title`, `body` |
| Add comment | `add_issue_comment` | `owner`, `repo`, `issue_number`, `body` |
| List comments | `get_issue_comments` | `owner`, `repo`, `issue_number` |
| List labels | `list_labels` | `owner`, `repo` |

## Label Taxonomy

### Type Labels (exactly one per issue)

| Config Key | Label String |
|---|---|
| `bug` | `bug` |
| `feature` | `enhancement` |
| `task` | `task` |
| `epic` | `epic` |
| `user_story` | `user story` |
| `test` | `testing` |

### Priority Labels (exactly one per issue)

| Config Key | Label String |
|---|---|
| `critical` | `priority: critical` |
| `high` | `priority: high` |
| `medium` | `priority: medium` |
| `low` | `priority: low` |

### Auto Labels (always applied)

- `hackathon`
- `agentic-devops`

## Field Rules

- `title`: concise, actionable (≤ 72 characters)
- `body`: use GitHub Markdown; include **Acceptance Criteria** section for features/stories
- `assignees`: array of GitHub usernames — resolve from `assignee_map` in config
- `labels`: combine type label + priority label + auto labels (minimum 4 labels)
- `state`: `open` or `closed`
- `milestone`: use sprint name from `sprint_map` in config if applicable

## Issue Body Template

```markdown
## Summary
<brief description of what needs to be done>

## Context
<why this is needed>

## Acceptance Criteria
- [ ] <criterion 1>
- [ ] <criterion 2>

## Notes
<any additional context, links, constraints>
```

## Constraints

- Labels must exist in the repo before assignment — use `list_labels` to verify
- Assignees must have repo access — check org membership if assignment fails
- Project board fields (Status, Priority, Sprint) are NOT set via the issues API — use `github-projects` skill
- `node_id` returned by `create_issue` is needed for `addProjectV2ItemById` — capture it
