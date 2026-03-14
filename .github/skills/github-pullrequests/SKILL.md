---
name: github-pullrequests
description: Manage GitHub Pull Requests — create, review, comment, request changes, approve, and merge. Use when the user asks to open a PR, post a code review, respond to review comments, resolve threads, or merge a branch into main.
argument-hint: "[open | review <#> | comment <#> | approve <#> | request-changes <#> | merge <#> | status <#>]"
---

# GitHub Pull Request Management Skill

Use this skill for all GitHub Pull Request operations via the `github` MCP server `pull_requests` toolset. Configuration lives in `github_devflow/config/github-config.yaml`.

## When To Use This Skill

- Open a new pull request from a branch
- List open PRs and their review status
- Post inline review comments on specific file/line positions
- Submit a full PR review (Approve / Request Changes / Comment)
- Resolve or unresolve review threads
- Merge a pull request
- Link a PR to an issue (via "Closes #N" in PR body)

## Operational Boundaries

- Always include "Closes #N" or "Fixes #N" in the PR body when the PR resolves a tracked issue — this auto-closes the issue on merge.
- For inline comments, the `commit_id` must be the latest commit SHA on the PR head branch.
- Default merge method: `squash` (from `pr_defaults.merge_method` in config).
- Default base branch: `main` (from `pr_defaults.base_branch` in config).
- After merge, confirm linked issues were auto-closed; update project board Status to "Done" if needed.
- Never merge a PR with failing CI or without at least one approving review (unless explicitly instructed).

## Standard Execution Flow

### Open PR
1. Confirm source branch and target branch.
2. Draft PR body using the template from `REFERENCE.md` — include "Closes #N" for all linked issues.
3. Resolve assignee GitHub username from `assignee_map` in config.
4. Call `create_pull_request`.
5. Add PR to project board if tracking it (see `github-projects` skill).

### Review PR
1. Call `get_pull_request` — read title, body, linked issues, head SHA.
2. Call `get_pull_request_files` — read changed files and patch content.
3. Post inline comments via `add_pull_request_review_comment` for specific findings.
4. Submit full review via `add_pull_request_review` with verdict: `APPROVE`, `REQUEST_CHANGES`, or `COMMENT`.

### Merge PR
1. Confirm all required reviews are approved and CI is passing.
2. Call `merge_pull_request` with `merge_method: squash`.
3. Confirm linked issues were auto-closed.
4. Update project board Status to "Done" for linked items if not auto-updated.

## Reference Material

- [references/REFERENCE.md](references/REFERENCE.md) — MCP tool names, review event types, merge methods, PR body template
- [references/WORKFLOWS.md](references/WORKFLOWS.md) — step-by-step procedures
- [references/TROUBLESHOOTING.md](references/TROUBLESHOOTING.md) — common failures and recovery

## Output Rules

- Always confirm with PR number and URL after creation.
- After review submission, state the verdict and number of inline comments posted.
- After merge, confirm the merge SHA and whether linked issues were closed.
