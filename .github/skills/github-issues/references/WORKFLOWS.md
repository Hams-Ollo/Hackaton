# GitHub Issues Skill Workflows

## New Issue Workflow

1. Ask for or infer: issue type, title, body/description, priority, assignee, sprint.
2. Resolve GitHub username from `assignee_map` in `github_devflow/config/github-config.yaml`.
3. Build labels array: type label + priority label + `auto_labels` (minimum 4 labels).
4. Draft the issue body using the template from `REFERENCE.md`.
5. Call `create_issue` → capture returned `number` and `node_id`.
6. Confirm with issue URL (format: `https://github.com/Terraformers-Anonymous/hackathon-project/issues/<number>`).
7. Add to project board: pass `node_id` to `github-projects` skill or call `addProjectV2ItemById` directly.
8. Set Status = "Todo" and Sprint field on the project board item.

## Update Issue Workflow

1. Confirm issue number.
2. Identify which fields change: state, labels, assignees, title, body, milestone.
3. Call `update_issue` with only the changed fields.
4. If the status semantics changed (e.g. work started → "In Progress"), update project board Status field.
5. Post a comment if the change is significant (state change, reassignment, scope change).

## Close Issue Workflow

1. Confirm the issue is resolved — linked PR is merged or work is verified done.
2. Call `update_issue` with `state: closed`.
3. Update project board Status to "Done" (via `github-projects` skill).
4. Post a closing comment summarizing what was done, linking the relevant PR or commit.

## Comment / Work Notes Workflow

1. Draft comment in professional past tense.
2. Include specific deliverables, links (PR number, commit SHA), and next steps if applicable.
3. Call `add_issue_comment`.
4. Confirm comment was posted with the comment URL.

## Bulk Triage Workflow

1. Call `list_issues` with `state: open` and `owner: Terraformers-Anonymous`, `repo: hackathon-project`.
2. Identify issues missing: priority label, assignee, or type label.
3. Show a table of proposed updates (issue number | title | missing fields | proposed values).
4. Wait for user approval.
5. Execute `update_issue` for each approved change.

## Label Setup Workflow (first-time)

If labels don't exist in the repo yet:
1. Call `list_labels` to see what exists.
2. For each missing label from the taxonomy in `REFERENCE.md`, create it via the GitHub UI or `labels` MCP toolset.
3. Confirm all labels exist before bulk issue creation.
