# DevFlow Suite — Copilot Instructions

## Project Overview

This is the **Terraformers Anonymous** hackathon project for the Microsoft Global Partner Hackathon (Capgemini team: Hans Havlik, Jamil Al Bouhairi, Ricardo Reyes-Jimenez, Uma Bharti).

**Use case:** A platform-agnostic developer toolsuite that integrates the development work surface with project management tracking through the GitHub Copilot chat interface in VS Code. Developers manage issues, PRs, code reviews, sprint boards, and work items entirely through natural language in Copilot Agent Mode — without leaving VS Code.

**Platform support:** GitHub (primary demo) and Azure DevOps (reference implementation). Swapping between platforms requires only changing which MCP server and config file is in use — the agent and skill UX is identical.

This project uses both the **GitHub MCP server** (`github`) and the **Azure DevOps MCP server** (`ado`). Always check if a relevant MCP tool exists before falling back to scripts or manual steps.

## Active Agents

| Agent | Platform | Use When |
|---|---|---|
| **GitHub Project Manager** | GitHub | Plan issues, groom backlog, query board state, sprint planning |
| **GitHub DevOps Engineer** | GitHub | Create/update issues, open/review/merge PRs, update board fields |
| **ADO Planner** | Azure DevOps | Plan ADO backlog, reconcile CSV, sprint planning |
| **ADO Executor** | Azure DevOps | Edit CSV, run sync scripts, push to ADO board |
| **Hackathon Codebase Reviewer** | Both | Full code audit, convention checks, sprint state report |

## Active Skills

| Skill | Platform | Use When |
|---|---|---|
| `github-issues` | GitHub | Create, update, close, label, assign GitHub Issues |
| `github-projects` | GitHub | Manage GitHub Projects v2 board fields (Status, Priority, Sprint) |
| `github-pullrequests` | GitHub | Open, review, comment, merge GitHub PRs |
| `ado-workitems` | Azure DevOps | Create, update, sync ADO work items via CSV pipeline |

## MCP Servers (both always active in `.vscode/mcp.json`)

| Server Key | Package / Endpoint | Auth | Domains |
|---|---|---|---|
| `github` | `https://api.githubcopilot.com/mcp/` | VS Code GitHub OAuth | issues, pull_requests, projects, repos, actions, labels |
| `ado` | `npx @azure-devops/mcp` | Browser Microsoft login (first use) | core, work, work-items, repositories, pipelines |

## Repository Structure

```
.github/
  agents/                     # VS Code Copilot custom agent personas
  skills/
    github-issues/             # GitHub Issues skill (create, update, close, label, assign)
    github-projects/           # GitHub Projects v2 skill (Status, Priority, Sprint fields)
    github-pullrequests/       # GitHub PR skill (open, review, merge)
    ado-workitems/             # ADO work item skill (CSV pipeline)
  instructions/                # Scoped editing rules
  workflows/                   # GitHub Actions (event-driven automation)
  scripts/                     # Orchestration scripts called by workflows
github_devflow/
  config/github-config.yaml   # GitHub platform config: org, project field IDs, labels, assignees
ado_backlog_pipeline/
  config/ado-config.yaml      # ADO platform config: org, project, fields, state maps
  data/backlog.csv             # Canonical CSV — push gate for ADO changes
  data/TODO.md                 # Sprint planning scratchpad (Copilot memory)
  data/WORK_NOTES.md           # Session work log (tag items with **ADO#ID**)
  scripts/                     # Python scripts: pull, sync, report, comment, set-priority
```

## Platform Swap

To switch from GitHub to ADO: invoke the **ADO Planner** or **ADO Executor** agent instead of GitHub agents. Both MCP servers run simultaneously — no config changes needed.

See `.github/instructions/platform-swap.instructions.md` for the full platform mapping table.

## GitHub Workflow (Copilot-native)

Developer says → Copilot calls GitHub MCP tools → GitHub Issues / Projects / PRs updated live.

Common phrases:
- *"Create a bug issue for X, assign to Jamil, high priority, sprint 2"* → GitHub DevOps Engineer
- *"Show me what's in progress on the board"* → GitHub Project Manager
- *"Review PR #5 and post inline comments"* → GitHub DevOps Engineer
- *"What issues are unassigned?"* → GitHub Project Manager
- *"Merge PR #8 and close the linked issue"* → GitHub DevOps Engineer

## ADO Pipeline — Copilot Memory System

Copilot reads these files as session memory. Keep them updated.
- `ado_backlog_pipeline/data/WORK_NOTES.md` — write session notes here, tag with `**ADO#ID**`
- `ado_backlog_pipeline/data/TODO.md` — sprint planning, items without `ADO#ID` become new board items
- Say **"sync my work notes"** → Copilot drafts Work Notes + CSV updates for each tagged item
- Say **"archive my session notes"** → moves Active Session to Archive, resets for next session

## GitHub Actions (Event-Driven Automation)

Actions complement Copilot — they handle the automated half; Copilot handles the developer-initiated half.
Actions do NOT use MCP — they use `GITHUB_TOKEN` and the GitHub REST/GraphQL API directly.

| Workflow | Trigger | Status |
|---|---|---|
| `ai-pr-review.yml` | PR opened/sync | ✅ functional (needs AI endpoint) |
| `add-to-project.yml` | Issue/PR opened | ✅ functional |
| `chatops-ai.yml` | `/ai` comment | ⚠️ stub |
| `release-notes.yml` | `v*` tag push | ⚠️ stub |

## Coding Conventions

- Keep all agent prompts in `prompts/` files — no inline f-string prompts in Python files
- All Azure OpenAI calls must use `response_format` with a JSON schema — no free-text parsing
- Use `os.getenv()` for all credentials — never hardcode keys, PATs, or endpoints
- GitHub Actions secrets are injected via `${{ secrets.SECRET_NAME }}` — never hardcoded in YAML
- `github_devflow/config/github-config.yaml` is the source of truth for GitHub field IDs and labels
- `ado_backlog_pipeline/config/ado-config.yaml` is the source of truth for ADO fields and mappings
- Set `_row_dirty=1` on any CSV row that needs to be pushed to ADO; scripts skip clean rows
- Never PATCH read-only ADO fields (see `read_only_ado_columns` in `ado-config.yaml`)
- Run all ADO pipeline scripts from the repository root so relative paths resolve correctly
- Never hardcode GitHub project node IDs, field IDs, or option IDs in skill or agent files
