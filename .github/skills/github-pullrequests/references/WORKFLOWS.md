# GitHub Pull Requests Skill Workflows

## Open PR Workflow

1. Confirm: source branch (head), target branch (base — default: `main`), linked issue number(s).
2. Draft PR title (concise, ≤ 72 chars, imperative mood: "Add auth timeout handling").
3. Draft PR body using the template from `REFERENCE.md` — include "Closes #N" for all linked issues.
4. Resolve assignee GitHub username from `assignee_map` in config.
5. Call `create_pull_request` → capture `number` and `node_id`.
6. Confirm with PR URL: `https://github.com/Terraformers-Anonymous/hackathon-project/pull/<number>`.
7. Post a comment on the linked issue: "PR #N opened for this issue."
8. Optionally add PR to project board (see `github-projects` skill).

## Review PR Workflow

1. Call `get_pull_request` — read: title, body, author, `head.sha`, linked issues.
2. Call `get_pull_request_files` — list changed files with patch content.
3. For each significant finding:
   - Identify file path and line number from the patch.
   - Call `add_pull_request_review_comment` with `commit_id = head.sha`, `path`, `line`, and `body`.
4. After all inline comments, call `add_pull_request_review` with:
   - All good → `event: APPROVE`, brief summary body
   - Minor issues → `event: COMMENT`, overall summary body
   - Blocking issues → `event: REQUEST_CHANGES`, list of required changes in body
5. State: "Posted N inline comments. Overall verdict: [APPROVE / REQUEST_CHANGES / COMMENT]."

## Merge PR Workflow

1. Call `get_pull_request_reviews` — confirm at least one `APPROVED` review with no outstanding `REQUEST_CHANGES`.
2. Confirm CI status with the user (or check via `actions` toolset if available).
3. Call `merge_pull_request` with `merge_method: squash` and a clean `commit_title`.
4. Confirm linked issues were auto-closed (GitHub auto-closes on merge when "Closes #N" is in PR body).
5. If issues were not auto-closed, call `update_issue` with `state: closed` for each.
6. Update project board Status to "Done" for linked items (see `github-projects` skill).

## Resolve Review Thread Workflow

1. Identify the thread — from context or by listing `get_pull_request_review_comments`.
2. Call `resolve_review_thread` with `thread_id`.
3. Post a reply comment confirming the change was addressed: "Addressed in commit <SHA>."

## Respond to Review Workflow

1. Read the review comments via `get_pull_request_review_comments`.
2. For each requested change: confirm it has been implemented in a new commit.
3. Post a reply to the relevant thread confirming the fix.
4. Call `resolve_review_thread` for each resolved thread.
5. Request a re-review by posting a PR comment: "All requested changes addressed. Ready for re-review."
