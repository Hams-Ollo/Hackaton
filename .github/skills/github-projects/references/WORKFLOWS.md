# GitHub Projects Skill Workflows

## First-Time Config Setup Workflow

Run this once after creating the project board — before any field updates:

1. Ask Copilot: *"List all fields on project 1 for org Terraformers-Anonymous"* (github MCP server).
2. Copy the returned `projectId` (PVT_...) into `project_fields.project_id` in config.
3. Copy Status `field_id` and all option IDs (Todo/In Progress/Done) into `project_fields.status`.
4. Copy Priority `field_id` and all option IDs into `project_fields.priority`.
5. Copy Sprint `field_id` into `project_fields.sprint.field_id`.
6. Commit the updated `github_devflow/config/github-config.yaml`.

## Add Issue to Board Workflow

1. Get issue `node_id` via `get_issue` (owner: Terraformers-Anonymous, repo: hackathon-project, issue_number: N).
2. Read `project_id` from config.
3. Call `addProjectV2ItemById(projectId, contentId: node_id)` → capture returned `itemId`.
4. Read `project_fields.status.field_id` and `options.todo` from config.
5. Call `updateProjectV2ItemFieldValue(projectId, itemId, fieldId, { singleSelectOptionId: options.todo })`.
6. If sprint is specified, run the Update Sprint workflow.

## Update Status Workflow

1. Identify the project item's `itemId` — query project items if unknown.
2. Read `project_fields.status.field_id` from config.
3. Map the desired status to `singleSelectOptionId` from `project_fields.status.options`:
   - "Todo" → `options.todo`
   - "In Progress" → `options.in_progress`
   - "Done" → `options.done`
4. Call `updateProjectV2ItemFieldValue(projectId, itemId, fieldId, { singleSelectOptionId: ... })`.
5. Confirm updated value.

## Update Sprint Workflow

1. Query the Sprint field to list current iteration IDs: ask Copilot "list iterations for project 1".
2. Match the user's sprint name to the correct `iterationId`.
3. Read `project_fields.sprint.field_id` from config.
4. Call `updateProjectV2ItemFieldValue(projectId, itemId, fieldId, { iterationId: ... })`.
5. Confirm updated value.

## Update Priority Workflow

1. Identify the project item's `itemId`.
2. Read `project_fields.priority.field_id` from config.
3. Map desired priority to `singleSelectOptionId` from `project_fields.priority.options`.
4. Call `updateProjectV2ItemFieldValue(projectId, itemId, fieldId, { singleSelectOptionId: ... })`.

## Sprint Progress Report Workflow

1. Query all project items with Status field values via `projects` toolset.
2. Count items per Status value: Todo, In Progress, Done.
3. Build a report table:

   | # | Title | Status | Assignee | Priority |
   |---|-------|--------|----------|----------|

4. Highlight items that have been "In Progress" for more than one sprint.
5. Identify items with no assignee or no Priority set.

## Close Sprint Workflow

1. Run Sprint Progress Report.
2. Move all "Done" items — confirm linked issues are closed.
3. Move unfinished items to the next sprint (Update Sprint workflow).
4. Report: completed / carried over / dropped.
