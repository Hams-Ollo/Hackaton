# DevFlow Suite  Architecture and Developer Guide

> Last updated: March 2026 | Team Terraformers Anonymous | Microsoft Global Partner Hackathon

---

## 1. Overview

DevFlow Suite is a **platform-agnostic developer toolsuite** that integrates a developer's code editor with project management tracking through natural language. Developers manage GitHub Issues, Pull Requests, sprint boards, and ADO work items entirely through the GitHub Copilot chat interface in VS Code  without leaving the editor.

### Core Principle

> The developer's intent is expressed in natural language. The system translates that intent into the correct sequence of API calls against the correct project management backend.

There is no new UI to learn, no browser tab to open, and no manual copy-paste of IDs. The only interface is the Copilot chat panel.

---

## 2. System Layers

The system has three distinct layers that compose together:

```
Layer 1  Copilot Agent Layer (VS Code)
    Agents + Skills + Instructions
    Persona selection determines which platform is targeted

Layer 2  MCP Layer (Protocol Bridge)
    Official vendor MCP servers translate agent tool calls
    into live REST/GraphQL API calls against GitHub or ADO

Layer 3  Event Layer (GitHub Actions)
    Git-event-driven automation that runs in parallel
    with Copilot-initiated changes
```

---

## 3. Layer 1: Copilot Agent Layer

### 3.1 Agents

Agents are custom Copilot personas defined as `.agent.md` files in `.github/agents/`. Each agent has:

- A **name** and **description** used by Copilot to match the right agent to user intent
- A **tools** array listing which VS Code built-in tools are available (MCP server tools are auto-available and do NOT need to be declared here)
- A **handoffs** block defining natural transition points to other agents
- A **markdown body** that is the system prompt  it tells the agent its responsibilities, operating rules, and which config files and skills to consult

| Agent | File | Platform | Role |
|---|---|---|---|
| GitHub Project Manager | `GitHub Project Manager.agent.md` | GitHub | Planning  reads board state, grooms backlog, proposes work |
| GitHub DevOps Engineer | `GitHub DevOps Engineer.agent.md` | GitHub | Execution  creates issues, opens PRs, updates board fields |
| ADO Planner | `ADO Planner.agent.md` | Azure DevOps | Planning  reads CSV and ADO state, proposes work |
| ADO Executor | `ADO Executor.agent.md` | Azure DevOps | Execution  edits CSV, runs sync scripts, pushes to ADO |
| Hackathon Codebase Reviewer | `Codebase Review.agent.md` | Both | Audit  reviews code, conventions, sprint state |

**Platform selection is entirely driven by which agent the developer invokes.** Both MCP servers are always connected. There is no config switch.

### 3.2 Skills

Skills are reusable playbooks referenced by agents. They follow the agentskills.io open standard:
- `SKILL.md`  thin entrypoint with frontmatter (`name`, `description`, `argument-hint`)
- `references/REFERENCE.md`  MCP tool names, data types, node ID formats
- `references/WORKFLOWS.md`  step-by-step procedures for common operations
- `references/TROUBLESHOOTING.md`  known failure modes and fixes

| Skill | Directory | Platform | Purpose |
|---|---|---|---|
| github-issues | `.github/skills/github-issues/` | GitHub | Issue lifecycle management |
| github-projects | `.github/skills/github-projects/` | GitHub | Projects v2 board field management |
| github-pullrequests | `.github/skills/github-pullrequests/` | GitHub | PR lifecycle management |
| ado-workitems | `.github/skills/ado-workitems/` | Azure DevOps | Work item CSV pipeline |

### 3.3 Instructions

Scoped instruction files in `.github/instructions/` provide convention rules that are injected into Copilot context when the `applyTo` glob matches the files being edited.

| File | Scope | Content |
|---|---|---|
| `github-devflow.instructions.md` | `.github/skills/github-*/**` | 13 GitHub DevFlow convention rules |
| `platform-swap.instructions.md` | `.vscode/mcp.json` | GitHub <-> ADO concept mapping table, swap contract |
| `ado-backlog-pipeline.instructions.md` | `ado_backlog_pipeline/**` | ADO CSV pipeline rules |
| `copilot-customizations.instructions.md` | `.github/**/*.md` | Agent/skill/instruction authoring rules |
| `mcp.instructions.md` | `.vscode/mcp.json` | MCP server configuration rules |

### 3.4 Config Files

Two YAML files serve as the single source of truth for platform-specific IDs and mappings. Agents always read these before any write operation.

**`github_devflow/config/github-config.yaml`**
- GitHub org, repo, and project number
- GitHub Projects v2 GraphQL node IDs (project_id, field_ids, option IDs)  blank on first clone, populated via one-time MCP query
- Label taxonomy (issue type labels, priority labels, auto-apply labels)
- Assignee map (display name -> GitHub username)
- Sprint map (sprint name -> number)
- PR defaults (merge strategy, base branch)

**`ado_backlog_pipeline/config/ado-config.yaml`**
- ADO org URL and project name
- Field name registry (display names -> internal field names)
- State maps (issue type -> ADO work item type)
- Read-only field list (fields that must never be PATCHed)
- Iteration map (sprint name -> ADO iteration path)
- Assignee map (display name -> ADO email)

---

## 4. Layer 2: MCP Layer

### 4.1 What is MCP?

Model Context Protocol (MCP) is an open standard that allows AI models (like GitHub Copilot) to call external tools via a standardized interface. Each MCP server exposes a set of named tools that the model can invoke, passing structured parameters and receiving structured responses.

In VS Code, MCP servers are configured in `.vscode/mcp.json`. VS Code automatically makes all tools from all configured servers available to agents in Agent Mode  no explicit declaration needed in agent files.

### 4.2 GitHub MCP Server

- **Source:** Official  `github/github-mcp-server` (Go binary, MIT)
- **Transport:** HTTP remote at `https://api.githubcopilot.com/mcp/`
- **Auth:** VS Code GitHub OAuth  the developer's existing GitHub login, no PAT needed
- **Toolsets available:** `context`, `issues`, `pull_requests`, `projects`, `repos`, `labels`, `actions`, `notifications`, `git`

```json
"github": {
  "type": "http",
  "url": "https://api.githubcopilot.com/mcp/"
}
```

Key tools used by DevFlow agents:

| Tool | Toolset | Purpose |
|---|---|---|
| `create_issue` | issues | Create a GitHub Issue |
| `update_issue` | issues | Update state, labels, assignees, body |
| `add_issue_comment` | issues | Post a comment on an issue |
| `create_pull_request` | pull_requests | Open a PR |
| `add_pull_request_review` | pull_requests | Submit a PR review (Approve/Request Changes/Comment) |
| `merge_pull_request` | pull_requests | Merge a PR |
| `addProjectV2ItemById` | projects | Add an issue/PR to a Projects v2 board |
| `updateProjectV2ItemFieldValue` | projects | Set Status, Priority, Sprint on a board item |
| `list_labels` | labels | List all labels in the repo |

### 4.3 GitHub Projects v2  Important Constraint

GitHub Projects v2 uses the GraphQL API exclusively. The key implications:

1. **Everything requires a node ID.** Issues have a `node_id` (format `I_kgDO...`), project items have an `itemId` (format `PVTI_...`), fields have a `field_id` (format `PVTSSF_...` for single-select), and single-select options have an `optionId`.

2. **Adding to the board and updating fields are always two separate calls.** You cannot add an item and set its fields in one operation:
   - Call 1: `addProjectV2ItemById` (projectId + contentId)  returns `itemId`
   - Call 2: `updateProjectV2ItemFieldValue` (projectId + itemId + fieldId + value)  once per field

3. **Sprint iteration IDs are dynamic.** Each sprint's `iterationId` changes. Always query the Sprint field for the current iteration ID rather than hardcoding.

4. **Field IDs must be pre-populated in config.** The `github_devflow/config/github-config.yaml` has blank placeholders. Before any board write can succeed, these must be populated by querying the live project (one-time setup).

### 4.4 ADO MCP Server

- **Source:** Official  `microsoft/azure-devops-mcp` (Node.js, MIT)
- **Transport:** stdio via `npx @azure-devops/mcp`
- **Auth:** Browser-based Microsoft login on first use; VS Code prompts for org name and PAT
- **Domains configured:** `core`, `work`, `work-items`, `repositories`, `pipelines`

```json
"ado": {
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "@azure-devops/mcp", "${input:ado_org}", "-d", "core", "work", "work-items", "repositories", "pipelines"],
  "env": { "ADO_PAT": "${input:ado_pat}" }
}
```

### 4.5 Platform Swap Contract

Both MCP servers are active simultaneously. The developer selects a platform by choosing which agent to invoke  not by changing any configuration. The following table maps equivalent concepts across platforms:

| Concept | GitHub | Azure DevOps |
|---|---|---|
| Work item | Issue | Work Item (Task/Bug/User Story) |
| Board | GitHub Projects v2 | ADO Board / Backlog |
| Sprint | Iteration (Projects v2 field) | Iteration Path |
| Status | Status field (single-select) | System.State |
| Priority | Priority field (single-select) | Priority field |
| PR | Pull Request | Pull Request (ADO Repos) |
| Planning agent | GitHub Project Manager | ADO Planner |
| Execution agent | GitHub DevOps Engineer | ADO Executor |
| Config file | `github_devflow/config/github-config.yaml` | `ado_backlog_pipeline/config/ado-config.yaml` |
| Write mechanism | GitHub MCP tools (live) | CSV pipeline + Python scripts |

---

## 5. Layer 3: GitHub Actions

GitHub Actions provide event-driven automation that runs server-side in response to git events. They complement the Copilot layer  Copilot handles developer-initiated changes, Actions handle the automated half.

Actions do NOT use MCP. They use the built-in `GITHUB_TOKEN` and the GitHub REST/GraphQL API directly.

### 5.1 Workflow Inventory

**`add-to-project.yml`**  Status: Functional
- Trigger: Issue or PR opened / labeled
- Action: Adds the item to GitHub Project #1 automatically
- No AI involvement  pure automation

**`ai-pr-review.yml`**  Status: Functional (needs endpoint secret)
- Trigger: PR opened or synchronized
- Action: Fetches the PR diff, calls the PR review agent endpoint (`AI_PR_REVIEW_FUNC_URL`), posts findings as a PR comment
- The agent endpoint must be deployed separately; it is not part of this repository

**`chatops-ai.yml`**  Status: Stub
- Trigger: Issue or PR comment containing `/ai`
- Action: `chatops_router.py` (not yet implemented) would parse the command and route to the correct agent
- Commands planned: `/ai review`, `/ai triage`, `/ai standup`

**`release-notes.yml`**  Status: Stub
- Trigger: Push to a `v*` tag
- Action: Would call a release notes generation script (not yet created)

### 5.2 Required GitHub Actions Secrets

| Secret | Required By | Description |
|---|---|---|
| `AI_PR_REVIEW_FUNC_URL` | `ai-pr-review.yml` | Deployed PR review agent URL |
| `AI_CHATOPS_FUNC_URL` | `chatops-ai.yml` | Deployed ChatOps agent URL |
| `PROJECT_TOKEN` | `add-to-project.yml` | GitHub PAT with `project` scope |

---

## 6. ADO Backlog Pipeline (Local CSV Layer)

The ADO integration uses a local-first CSV pipeline operated by the ADO Planner and ADO Executor agents. This approach gives developers full visibility and control over what gets pushed to ADO.

### 6.1 Data Flow

```
ADO Boards
    |
    | pull-ado-workitems.py (reads live ADO state)
    v
backlog.csv (43-column canonical representation)
    |
    | Copilot edits rows, sets _row_dirty=1
    v
sync-ado-workitems.py (PATCHes rows where _row_dirty=1)
    |
    v
ADO Boards (updated)
```

### 6.2 Python Scripts

| Script | Purpose |
|---|---|
| `pull-ado-workitems.py` | Pull current ADO board state into backlog.csv |
| `sync-ado-workitems.py` | Push rows where `_row_dirty=1` to ADO |
| `commit-ado-sync.py` | Git commit wrapper that tags commits with `AB#ID` |
| `generate-ado-report.py` | Generate Markdown sprint status report |
| `add-ado-comment.py` | Post a comment on an ADO work item |
| `set-priority.py` | Bulk-set priority on filtered work items |
| `migrate-csv-schema.py` | Migrate backlog.csv when schema changes |

### 6.3 Copilot Memory Files

| File | Purpose |
|---|---|
| `ado_backlog_pipeline/data/TODO.md` | Sprint scratchpad  items without `ADO#ID` become new work items |
| `ado_backlog_pipeline/data/WORK_NOTES.md` | Session work log  tag entries with `**ADO#ID**` for sync |

**Session workflow:**
1. Developer says "sync my work notes"  Copilot reads WORK_NOTES.md and drafts CSV row updates
2. Developer reviews the diff in backlog.csv
3. Rows marked `_row_dirty=1`  Copilot runs `sync-ado-workitems.py`
4. Commit with `AB#<ID>`  `commit-ado-sync.py` auto-updates ADO state

---

## 7. First-Run Setup Checklist

### GitHub Platform

- [ ] Clone the repo and open in VS Code
- [ ] Sign in to GitHub in VS Code (if not already)
- [ ] Open Copilot Chat, switch to Agent Mode  the `github` MCP server connects automatically
- [ ] Invoke **GitHub Project Manager**: "List all fields on project 1 for org Terraformers-Anonymous"
- [ ] Copy the returned `PVT_...` project_id and all `PVTSSF_...` field IDs into `github_devflow/config/github-config.yaml`
- [ ] Confirm GitHub usernames in `assignee_map` for all team members
- [ ] Verify that `hackathon` and `agentic-devops` labels exist in the repo (create if missing)

### ADO Platform

- [ ] Edit `ado_backlog_pipeline/config/ado-config.yaml`  set `ado.org_url` and `ado.project`
- [ ] Update `assignee_map` with real team member ADO email addresses
- [ ] On first Copilot Agent Mode use with ADO: VS Code will prompt for org name and PAT
- [ ] Run `pull-ado-workitems.py` from the repo root to populate `backlog.csv` with current board state

### GitHub Actions

- [ ] Add required secrets in repo Settings -> Secrets and variables -> Actions
- [ ] Confirm `add-to-project.yml` is adding new issues to Project #1

---

## 8. Key Design Decisions and Rationale

### Why VS Code Copilot Agents instead of a standalone web app?

Developers already live in VS Code. Any solution that requires opening a browser or a separate UI introduces the context switch we're trying to eliminate. VS Code Copilot Agent Mode with custom agents and MCP servers gives us a zero-install, zero-new-UI experience that piggybacks on the developer's existing toolchain.

### Why official vendor MCP servers instead of custom integrations?

Both GitHub and Microsoft publish and maintain official MCP servers:
- `github/github-mcp-server`  official, MIT, actively maintained
- `microsoft/azure-devops-mcp`  official, MIT, actively maintained

Using vendor-official servers means we inherit all API coverage, authentication handling, and future updates for free. Custom integrations would require significant ongoing maintenance.

### Why YAML config files for field IDs instead of querying dynamically every time?

GitHub Projects v2 GraphQL node IDs (`PVT_...`, `PVTSSF_...`) are stable and do not change once a project is created. Caching them in a committed YAML file avoids an extra API round-trip on every write operation and makes the config auditable and reviewable in PRs.

Sprint iteration IDs are the exception  they change each sprint and are always queried dynamically.

### Why a CSV pipeline for ADO instead of direct MCP calls?

The ADO CSV pipeline predates the dual-platform pivot and provides a useful human review layer  developers can see exactly what will be pushed to ADO before it happens. The ADO MCP server now provides a direct live-write path as well, giving teams the choice of pipeline (reviewed, auditable) vs. direct (fast, conversational).

### Why are GitHub Actions and Copilot agents separate?

They serve different triggers:
- **Copilot agents** handle developer-initiated work (explicit requests in chat)
- **GitHub Actions** handle git-event-driven automation (implicit, always-on)

They are complementary, not competing. A PR opened by a developer triggers the Actions review workflow automatically; the developer can also ask Copilot to review it conversationally.

---

## 9. Known Gaps and Open Work

| # | Gap | Severity | Owner |
|---|---|---|---|
| 1 | `github-config.yaml` project field IDs are empty  blocks all board writes | High | First-run setup |
| 2 | GitHub assignee usernames are placeholders | High | Team confirmation needed |
| 3 | `chatops_router.py` is an empty stub | High | Ricardo |
| 4 | `chatops-ai.yml` uses `echo` placeholder | High | Ricardo |
| 5 | `release-notes.yml` calls a script that does not exist | High | Ricardo |
| 6 | `ado-config.yaml` org URL is still `RARJ-CAP` placeholder | High | Hans |
| 7 | `prompts/*.md` files are fragments (< 200 bytes) | Medium | Jamil / Uma |
| 8 | PR review agent endpoint not deployed | Medium | Team |

---

## 10. Repository Structure Reference

```
hackathon-project/
|
+-- .github/
|   +-- agents/
|   |   +-- GitHub Project Manager.agent.md
|   |   +-- GitHub DevOps Engineer.agent.md
|   |   +-- ADO Planner.agent.md
|   |   +-- ADO Executor.agent.md
|   |   +-- Codebase Review.agent.md
|   |
|   +-- skills/
|   |   +-- github-issues/
|   |   |   +-- SKILL.md
|   |   |   +-- references/
|   |   |       +-- REFERENCE.md
|   |   |       +-- WORKFLOWS.md
|   |   |       +-- TROUBLESHOOTING.md
|   |   +-- github-projects/      (same structure)
|   |   +-- github-pullrequests/  (same structure)
|   |   +-- ado-workitems/        (same structure)
|   |
|   +-- instructions/
|   |   +-- github-devflow.instructions.md
|   |   +-- platform-swap.instructions.md
|   |   +-- ado-backlog-pipeline.instructions.md
|   |   +-- copilot-customizations.instructions.md
|   |   +-- mcp.instructions.md
|   |
|   +-- workflows/
|   |   +-- add-to-project.yml
|   |   +-- ai-pr-review.yml
|   |   +-- chatops-ai.yml
|   |   +-- release-notes.yml
|   |
|   +-- scripts/
|   |   +-- call_pr_review.py
|   |   +-- chatops_router.py
|   |
|   +-- copilot-instructions.md   (global Copilot instructions)
|
+-- .vscode/
|   +-- mcp.json                  (github + ado MCP server config)
|
+-- github_devflow/
|   +-- config/
|       +-- github-config.yaml
|
+-- ado_backlog_pipeline/
|   +-- config/ado-config.yaml
|   +-- data/
|   |   +-- backlog.csv
|   |   +-- TODO.md
|   |   +-- WORK_NOTES.md
|   +-- scripts/                  (9 Python scripts)
|   +-- prompts/                  (ADO session sync prompts)
|   +-- docs/
|
+-- docs/
|   +-- architecture.md           (this file)
|   +-- guides/
|
+-- README.md
+-- requirements.txt
```

---

## 11. Feedback and Open Questions for Team Review

These are open questions we'd like feedback on before the hackathon demo:

1. **GitHub field IDs**  Has anyone connected to the GitHub MCP and queried Project #1's field IDs yet? These need to be in the config before any demo of board writes.

2. **ADO org**  What is the correct Azure DevOps org URL and project name to use? The `ado-config.yaml` currently has a placeholder.

3. **Team GitHub usernames**  Can Jamil, Ricardo, and Uma confirm their GitHub usernames so we can populate `assignee_map`?

4. **PR review agent**  Is there a deployed endpoint we can point `AI_PR_REVIEW_FUNC_URL` to, or should we stub the Actions workflow for the demo?

5. **Demo scope**  Should we demo both platforms in the same session (GitHub first, then ADO swap), or focus on GitHub only for the hackathon presentation?

6. **ChatOps**  Is `/ai comment` ChatOps a nice-to-have for the demo, or a hard requirement? It currently blocks on `chatops_router.py` being implemented.
