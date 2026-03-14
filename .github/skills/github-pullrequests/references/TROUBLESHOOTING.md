# GitHub Pull Requests Skill Troubleshooting

## Common Failures

### PR creation fails — branch not found
The source branch does not exist or has not been pushed to the remote.
Verify with: ask Copilot "list branches for Terraformers-Anonymous/hackathon-project" via the github MCP server.
Push the branch first, then retry `create_pull_request`.

### Inline comment fails — line not in diff
The line number must be within the visible diff for the given commit.
Call `get_pull_request_files` to see the exact diff and pick a valid line number from the patch.
Only lines prefixed with `+` or unchanged context lines can be commented on.

### commit_id rejected for inline comment
The `commit_id` must be the latest commit SHA on the PR head branch.
Get it from `get_pull_request` → `head.sha`. Do not use any other commit SHA.

### Review submission fails — PR already merged or closed
`add_pull_request_review` only works on open PRs.
Verify PR state with `get_pull_request` first.

### Merge fails — required reviews not satisfied
Branch protection rules require at least one approving review.
Call `get_pull_request_reviews` to check current review states.
If no approvals exist, post a review with `event: APPROVE` first.

### Merge fails — CI checks failing
GitHub branch protection may require passing status checks.
Check workflow run status via `actions` toolset or ask the user to check the Checks tab.

### Linked issue not auto-closed after merge
The "Closes #N" keyword must appear in the PR **body** (not a comment, not the title).
Call `get_pull_request` to confirm the body contains the closing keyword.
If missing, close the issue manually: call `update_issue` with `state: closed`.

### resolve_review_thread fails — thread not found
The `thread_id` is the review thread node ID. Get it from `get_pull_request_review_comments` → `pull_request_review_id` is not the thread ID.
Query the review threads directly and identify the correct `id` field.

## Recovery Pattern

1. Call `get_pull_request` to confirm current PR state (open/closed/merged, head SHA, review state).
2. Call `get_pull_request_reviews` to see review status.
3. Retry the failed operation with corrected parameters.
4. If PR was merged with issues unresolved, handle them separately via `github-issues` skill.
