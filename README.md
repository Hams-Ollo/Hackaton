# DevFlow Suite

> **Microsoft Global Partner Hackathon  Capgemini  Team Terraformers Anonymous**

[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-powered-2088FF?logo=github-actions&logoColor=white)](https://github.com/Terraformers-Anonymous/hackathon-project/actions)
[![VS Code Copilot](https://img.shields.io/badge/VS_Code-Copilot_Agents-007ACC?logo=visual-studio-code&logoColor=white)](https://code.visualstudio.com/docs/copilot/copilot-customization)
[![GitHub MCP](https://img.shields.io/badge/GitHub_MCP-Official-181717?logo=github&logoColor=white)](https://github.com/github/github-mcp-server)
[![Azure DevOps MCP](https://img.shields.io/badge/ADO_MCP-Official-0078D4?logo=azure-devops&logoColor=white)](https://github.com/microsoft/azure-devops-mcp)

---

## The Problem We're Solving

Developers lose significant time **context-switching** between their code editor and external project management tools  opening a browser to file a ticket, updating a sprint board, posting a PR review, or checking what's blocked. That context switch breaks flow and adds friction to every developer interaction with the team.

**DevFlow Suite collapses that context switch to zero.**

Everything  creating issues, updating sprint boards, opening PRs, reviewing code, syncing work items  happens through **natural language in the GitHub Copilot chat panel inside VS Code**. No browser. No tab switch. No manual copy-paste of IDs.

The platform is **swappable**: the same developer UX works against **GitHub Projects** or **Azure DevOps Boards**. You change which agent you invoke, not how you work.

---

## How It Works

```
  Developer types in VS Code Copilot Chat
              |
              v
  +----------------------------------------------------+
  |          VS Code Copilot Agent Mode                |
  |                                                    |
  |  GitHub Project Manager  --|                       |
  |  GitHub DevOps Engineer  --+-- reads skills/       |
  |  ADO Planner             --+-- reads instructions/ |
  |  ADO Executor            --+-- reads config YAMLs  |
  |  Codebase Reviewer       --|                       |
  +------------+-------------------------------------------+
               |  MCP tool calls (auto-routed by server)
       +-------+--------+
       v                v
  +----------+    +---------------+
  |  GitHub  |    |  Azure DevOps |
  |  MCP     |    |  MCP          |
  | (HTTP,   |    | (npx, browser |
  |  OAuth)  |    |  login)       |
  +----+-----+    +------+--------+
       |                 |
       v                 v
  GitHub Issues     ADO Work Items
  Projects v2       ADO Boards
  Pull Requests     ADO Repos
  Labels/Milestones ADO Pipelines

  +----------------------------------------------------+
  |          GitHub Actions (event-driven)             |
  |  PR opened  -> AI review comment posted            |
  |  Issue opened -> auto-added to project board       |
  |  /ai comment -> ChatOps routing                    |
  |  v* tag push -> release notes generation           |
  +----------------------------------------------------+
```

---

## Agents

Five custom Copilot agents live in [`.github/agents/`](.github/agents/). Invoke any from Copilot Agent Mode in VS Code.

| Agent | Platform | Use It For |
|---|---|---|
| **GitHub Project Manager** | GitHub | Query board state, groom backlog, plan sprint, decompose epics |
| **GitHub DevOps Engineer** | GitHub | Create/update issues, open/review/merge PRs, update board fields |
| **ADO Planner** | Azure DevOps | Plan ADO backlog, reconcile CSV, sprint planning |
| **ADO Executor** | Azure DevOps | Edit CSV, run sync scripts, push to ADO board |
| **Hackathon Codebase Reviewer** | Both | Full code audit, convention checks, sprint state report |

### Example Phrases

```
"Create a high-priority bug for the null pointer on login, assign to Jamil, sprint 2"
"Show me everything in-progress on the board right now"
"Open a PR from feature/auth to main -- it closes issue #14"
"Review PR #7 and post inline comments on any logic issues"
"What issues are unassigned?"
"Sync my work notes to ADO"
"Run a full sprint state report"
```

---

## Skills

Four skills provide step-by-step playbooks that agents reference during execution.

| Skill | Platform | Capabilities |
|---|---|---|
| [`github-issues`](.github/skills/github-issues/SKILL.md) | GitHub | Create, update, label, assign, close issues |
| [`github-projects`](.github/skills/github-projects/SKILL.md) | GitHub | Add items to board, set Status / Priority / Sprint fields |
| [`github-pullrequests`](.github/skills/github-pullrequests/SKILL.md) | GitHub | Open, review, comment, approve, merge PRs |
| [`ado-workitems`](.github/skills/ado-workitems/SKILL.md) | Azure DevOps | Create, update, sync ADO work items via CSV pipeline |

---

## MCP Servers

Both servers are always active simultaneously in [`.vscode/mcp.json`](.vscode/mcp.json).

| Server | Transport | Auth | Domains |
|---|---|---|---|
| `github` | HTTP remote  `https://api.githubcopilot.com/mcp/` | VS Code GitHub OAuth  no PAT needed | issues, pull_requests, projects, repos, labels, actions |
| `ado` | stdio via `npx @azure-devops/mcp` | Browser Microsoft login (first use) | core, work, work-items, repositories, pipelines |

**Platform swap:** Call a GitHub agent and GitHub MCP tools activate. Call an ADO agent and ADO MCP tools activate. No config change needed. See the [platform swap guide](.github/instructions/platform-swap.instructions.md).

---

## GitHub Actions

Event-driven workflows run in parallel with Copilot-initiated changes.

| Workflow | Trigger | Status |
|---|---|---|
| [`add-to-project.yml`](.github/workflows/add-to-project.yml) | Issue or PR opened | Functional |
| [`ai-pr-review.yml`](.github/workflows/ai-pr-review.yml) | PR opened / updated | Functional  needs `AI_PR_REVIEW_FUNC_URL` secret |
| [`chatops-ai.yml`](.github/workflows/chatops-ai.yml) | `/ai` comment | Stub |
| [`release-notes.yml`](.github/workflows/release-notes.yml) | `v*` tag push | Stub |

---

## Repository Map

```
.github/
  agents/                     # 5 Copilot custom agents (.agent.md)
  skills/
    github-issues/             # GitHub Issues skill
    github-projects/           # GitHub Projects v2 skill
    github-pullrequests/       # GitHub PR skill
    ado-workitems/             # ADO work item skill
  instructions/                # 5 scoped instruction files
  workflows/                   # GitHub Actions
  scripts/                     # Python orchestration scripts for Actions

github_devflow/
  config/github-config.yaml   # GitHub platform config: org, project fields, labels, assignees

ado_backlog_pipeline/
  config/ado-config.yaml      # ADO platform config: org, project, fields, state maps
  data/backlog.csv             # Canonical CSV -- ADO push gate
  data/TODO.md                 # Sprint scratchpad (Copilot reads as memory)
  data/WORK_NOTES.md           # Session work log (tag items with ADO#ID)
  scripts/                     # 9 Python scripts: pull, sync, report, comment...
  prompts/                     # Prompt files for ADO session sync operations

docs/
  architecture.md              # Full developer architecture guide
  guides/                      # Operational runbooks
```

---

## Getting Started

### 1. Clone and Install

```bash
git clone https://github.com/Terraformers-Anonymous/hackathon-project.git
cd hackathon-project
pip install -r requirements.txt
```

### 2. Connect the GitHub MCP Server

No setup needed. The `github` MCP server uses VS Code's built-in GitHub OAuth.

1. Open VS Code -> **Copilot Chat** -> switch to **Agent Mode**
2. VS Code connects to `https://api.githubcopilot.com/mcp/` automatically using your GitHub login

### 3. Connect the ADO MCP Server (first use only)

On first use VS Code will prompt for:
- Your ADO org name (e.g. `my-org`)
- Your ADO PAT (Work Items: Read & Write scope)

### 4. Populate GitHub Project Field IDs (one-time)

`github_devflow/config/github-config.yaml` has blank field ID placeholders. Populate them once:

```
(In GitHub Project Manager agent mode)
"List all fields on project 1 for org Terraformers-Anonymous"
```

Copy the returned `PVT_...` and `PVTSSF_...` IDs into the config file.

### 5. Configure ADO Connection

Edit [`ado_backlog_pipeline/config/ado-config.yaml`](ado_backlog_pipeline/config/ado-config.yaml):
- Set `ado.org_url` to your Azure DevOps org URL
- Set `ado.project` to your ADO project name
- Update `assignee_map` with real team member emails

---

## Commit Conventions

```bash
# Close a GitHub Issue on merge
git commit -m "feat: implement board sync Closes #12"

# Link to an ADO Work Item
git commit -m "fix: handle null diff edge case AB#42"
```

`Closes #N` auto-closes the GitHub Issue when the PR merges to main.
`AB#ID` triggers the Azure Boards GitHub App to transition the work item state.

---

## Team

| Name | GitHub | Focus |
|---|---|---|
| **Hans Havlik** | [@Hams-Ollo](https://github.com/Hams-Ollo) | Architecture, ADO Pipeline, MCP Config |
| **Jamil Al Bouhairi** | -- | Agent Development, Prompt Design |
| **Ricardo Reyes-Jimenez** | -- | GitHub Actions, Infrastructure |
| **Uma Bharti** | -- | Skills, Instructions, Platform Swap |

**Organization:** [Terraformers-Anonymous](https://github.com/Terraformers-Anonymous)

---

## Further Reading

- [Architecture and Developer Guide](docs/architecture.md)
- [Platform Swap Reference](.github/instructions/platform-swap.instructions.md)
- [GitHub DevFlow Conventions](.github/instructions/github-devflow.instructions.md)
- [ADO Pipeline Guide](ado_backlog_pipeline/docs/ADO_AUTOMATION_PIPELINE_GUIDE.md)

---

## License

[MIT](LICENSE) (c) 2026 Terraformers Anonymous
