# GitHub Pull Requests Skill Reference

## Runtime Layout

- Skill entrypoint: `.github/skills/github-pullrequests/SKILL.md`
- Config: `github_devflow/config/github-config.yaml`
- MCP server: `github` `pull_requests` and `repos` toolsets
- Fixed owner: `Terraformers-Anonymous`
- Fixed repo: `hackathon-project`
- Default base branch: `main`
- Default merge method: `squash`

## MCP Tool Names (github server, pull_requests toolset)

| Operation | Tool Name | Key Parameters |
|---|---|---|
| Get PR | `get_pull_request` | `owner`, `repo`, `pull_number` |
| List PRs | `list_pull_requests` | `owner`, `repo`, `state`, `base`, `head` |
| Create PR | `create_pull_request` | `owner`, `repo`, `title`, `body`, `head`, `base`, `assignees[]`, `draft` |
| Get PR files | `get_pull_request_files` | `owner`, `repo`, `pull_number` |
| Get PR reviews | `get_pull_request_reviews` | `owner`, `repo`, `pull_number` |
| Get review comments | `get_pull_request_review_comments` | `owner`, `repo`, `pull_number` |
| Add inline comment | `add_pull_request_review_comment` | `owner`, `repo`, `pull_number`, `body`, `path`, `line`, `commit_id` |
| Submit review | `add_pull_request_review` | `owner`, `repo`, `pull_number`, `event`, `body`, `comments[]` |
| Merge PR | `merge_pull_request` | `owner`, `repo`, `pull_number`, `merge_method`, `commit_title` |
| Resolve thread | `resolve_review_thread` | `owner`, `repo`, `pull_number`, `thread_id` |

## Review Event Types

| Event | Meaning | When to Use |
|---|---|---|
| `APPROVE` | Approve PR for merge | All findings resolved, code is correct |
| `REQUEST_CHANGES` | Block merge, require changes | Blocking issues found |
| `COMMENT` | Comment without approving or blocking | Minor suggestions, questions |

## Merge Methods

| Method | When to Use |
|---|---|
| `squash` | Default — collapses all commits into one clean commit on base branch |
| `merge` | Preserves full commit history (merge commit) |
| `rebase` | Replays commits on top of base branch — linear history |

## Closing Keywords (in PR body)

These auto-close the linked issue when the PR is merged into the default branch:
- `Closes #N`
- `Fixes #N`
- `Resolves #N`

Multiple issues: `Closes #12, Closes #15`

## PR Body Template

```markdown
## Summary
<brief description of what this PR does>

## Changes
- <change 1>
- <change 2>

## Linked Issues
Closes #<issue_number>

## Testing
<how to verify this change works correctly>

## Notes
<any relevant context, deployment steps, or breaking changes>
```

## Inline Review Comment Rules

- `commit_id` must be the latest commit SHA on the PR head branch — get from `get_pull_request` → `head.sha`
- `path` must be the exact file path relative to repo root
- `line` must be a line number visible in the PR diff
- For multi-line comments, use `start_line` and `line` parameters
