---
name: GitHub DevFlow Rules
description: Rules for editing or operating the GitHub DevFlow toolsuite — github-config.yaml, GitHub skills, and GitHub agents. Applies to all GitHub platform skill and agent files.
applyTo: .github/skills/github-*/**
---

# GitHub DevFlow Rules

- Read `github_devflow/config/github-config.yaml` before any write operation to resolve field IDs, option IDs, and usernames.
- If the `project_fields` section has empty IDs, query the project via the `github` MCP server and update config first — never guess or hardcode node IDs.
- Never hardcode GitHub project node IDs (`PVT_...`), field IDs, or option IDs in skill files or agent instructions.
- GitHub usernames come from `assignee_map` in config — never use display names as assignee values.
- Label strings come from `issue_type_labels`, `priority_labels`, and `auto_labels` in config — never hardcode label strings inline.
- Always include `auto_labels` (`hackathon`, `agentic-devops`) on every created issue.
- Adding a project board item and setting its fields always requires two separate MCP calls — add first, then update.
- Status, Priority, and Sprint are project-level fields — they cannot be set via the GitHub Issues REST API.
- Assignees and Labels are issue-level fields — they cannot be set via the GitHub Projects v2 GraphQL API.
- Closing keywords (`Closes #N`, `Fixes #N`, `Resolves #N`) in a PR body auto-close linked issues on merge into the default branch.
- The `itemId` (PVTI_...) returned by `addProjectV2ItemById` is different from the issue `node_id` (I_kgDO...) — use the correct ID for each operation.
- Iteration IDs change each sprint — always query dynamically; never cache them in config.
- When in doubt about a field ID or option ID, re-query the project fields before writing.
