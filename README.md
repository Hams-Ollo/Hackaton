
# 🤖 Agentic DevOps Automation

> **Microsoft Global Partner Hackathon · Capgemini · Team Terraformers Anonymous**

[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-powered-2088FF?logo=github-actions&logoColor=white)](https://github.com/Terraformers-Anonymous/hackathon-project/actions)
[![Azure OpenAI](https://img.shields.io/badge/Azure_OpenAI-gpt--4o-0078D4?logo=microsoft-azure&logoColor=white)](https://azure.microsoft.com/en-us/products/ai-services/openai-service)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![VS Code Copilot](https://img.shields.io/badge/VS_Code-Copilot_Agents-007ACC?logo=visual-studio-code&logoColor=white)](https://code.visualstudio.com/docs/copilot/copilot-customization)

---

## ⚡ What This Does

A **two-tier agentic pipeline** that eliminates the repetitive DevOps and IT ops work that slows engineering teams down.

| Tier | Trigger | What Happens |
|---|---|---|
| 🤖 **VS Code Copilot Agents** | Developer asks in chat | Sprint planning, ADO board updates, work notes sync — all conversational |
| ⚙️ **GitHub Actions** | Git events (PR, issue, tag, comment) | AI reviews PRs, triages issues, updates ADO work items, generates release notes |

**Real Azure OpenAI calls. Real ADO integration. Real GitHub project board automation.**

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    GitHub Events                         │
│  PR opened │ Issue created │ /ai comment │ v* tag push  │
└──────────────────┬──────────────────────────────────────┘
                   │ GitHub Actions
                   ▼
┌─────────────────────────────────────────────────────────┐
│              .github/scripts/  (Python orchestration)    │
│  call_pr_review.py  │  chatops_router.py                 │
└──────────────────┬──────────────────────────────────────┘
                   │ HTTP POST
                   ▼
┌─────────────────────────────────────────────────────────┐
│              src/agents/  (Flask HTTP servers)           │
│  pr_review  │  issue_triage  │  log_analyst              │
│  release_notes  │  test_generator                        │
└────────┬──────────────────────────┬────────────────────-┘
         │ Azure OpenAI SDK          │ Azure AI Search
         ▼                           ▼
┌────────────────┐         ┌─────────────────────┐
│  gpt-4o        │         │  RAG Knowledge Base  │
│  (Azure AOAI)  │         │  (HNSW vector index) │
└────────────────┘         └─────────────────────┘
         │
         │ azure-devops SDK
         ▼
┌────────────────────────────────────────────────┐
│           Azure DevOps REST API v7.1            │
│  Work Items  │  Boards  │  Repos  │  Pipelines  │
└────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│          VS Code Copilot Agent Mode (Tier 1)             │
│  ADO Planner agent  │  ADO Executor agent                │
│  Codebase Review agent  │  ado-workitems skill           │
│  @azure-devops/mcp (live ADO tool access in chat)        │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Repository Map

```
.github/
  agents/               # VS Code Copilot custom agents (.agent.md)
  instructions/         # Scoped Copilot instructions (applyTo: glob)
  skills/               # Reusable Copilot skill workflows
  workflows/            # GitHub Actions (AI review, triage, ADO sync, ChatOps)
  scripts/              # Orchestration scripts called by workflows
  ISSUE_TEMPLATE/       # Bug + Feature issue templates (auto-triaged)
  PULL_REQUEST_TEMPLATE.md  # PR checklist with AB#ID field

src/agents/             # AI agent HTTP servers (Flask, one per use case)
  pr_review/            # POST /pr-review — reviews diffs, gates merge
  issue_triage/         # POST /triage — classifies issues, creates ADO items
  log_analyst/          # POST /analyze-logs — Azure Monitor log analysis
  release_notes/        # POST /release-notes — tag-triggered changelog
  test_generator/       # POST /generate-tests — unit test scaffolding

ado_backlog_pipeline/   # Copilot-native ADO board management bundle
  config/ado-config.yaml  # Single source of truth: org, fields, state maps
  data/backlog.csv        # Canonical 43-column CSV — ADO push gate
  data/TODO.md            # Sprint scratchpad (Copilot reads this)
  data/WORK_NOTES.md      # Session work log (tag items with ADO#ID)
  scripts/                # 9 Python scripts: pull, sync, commit-sync, report…
  prompts/                # Session sync, work item creation, commit message prompts

rag/ingest/             # Azure AI Search indexer (HNSW vector + semantic)
prompts/                # System/user prompts for each agent
infra/bicep/            # IaC for AOAI, AI Search, Key Vault, App Insights
docs/                   # Architecture docs, diagrams (Mermaid), guides
```

---

## 🚀 Quick Start

### 1️⃣ Clone & Install

```bash
git clone https://github.com/Terraformers-Anonymous/hackathon-project.git
cd hackathon-project
pip install -r requirements.txt
```

### 2️⃣ Configure Environment

```bash
cp ado_backlog_pipeline/.env.example ado_backlog_pipeline/.env
# Edit .env — fill in ADO_PAT, AZURE_OPENAI_*, AZURE_SEARCH_*, GITHUB_TOKEN
```

### 3️⃣ Add GitHub Actions Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Description |
|---|---|
| `ADO_PAT` | Azure DevOps PAT (Work Items: Read & Write) |
| `AZURE_OPENAI_ENDPOINT` | Your Azure OpenAI endpoint URL |
| `AZURE_OPENAI_KEY` | Your Azure OpenAI API key |
| `AZURE_OPENAI_DEPLOYMENT` | Deployment name (e.g. `gpt-4o`) |
| `AZURE_SEARCH_ENDPOINT` | Azure AI Search endpoint |
| `AZURE_SEARCH_KEY` | Azure AI Search admin key |
| `PROJECT_TOKEN` | GitHub PAT with `project` scope (for board automation) |
| `PROJECT_URL` | Your GitHub Project URL (e.g. `https://github.com/orgs/Terraformers-Anonymous/projects/1`) |
| `AI_PR_REVIEW_FUNC_URL` | Deployed PR Review agent URL |
| `AI_CHATOPS_FUNC_URL` | Deployed ChatOps agent URL |

### 4️⃣ Confirm ADO Config

Edit [`ado_backlog_pipeline/config/ado-config.yaml`](ado_backlog_pipeline/config/ado-config.yaml):
- Set `ado.org_url` to your actual Azure DevOps org
- Set `ado.project` to your ADO project name
- Update `assignee_map` with real team member emails

### 5️⃣ Start Using Copilot Agents in VS Code

Open VS Code → Copilot Chat → Agent Mode → select **ADO Planner** or type:
```
@ADO Planner what's in our current sprint?
@ADO Executor sync my work notes to ADO
```

---

## 🤖 VS Code Copilot Agents

| Agent | Purpose | Trigger Phrases |
|---|---|---|
| **ADO Planner** | Sprint planning, backlog grooming, work item decomposition | `what's in our sprint?`, `help me plan this week` |
| **ADO Executor** | Execute ADO changes via CSV — create, update, sync work items | `sync my work notes`, `update ADO from my notes` |
| **Codebase Review** | Full sprint audit — stubs, conventions, open issues, ADO accuracy | `review the codebase`, `sprint audit` |

**The `ado-workitems` skill** is available in all agents:
```
/ado-workitems new    # Draft a new work item row in backlog.csv
/ado-workitems sync   # Push dirty rows to ADO
/ado-workitems pull   # Pull latest ADO state into CSV
/ado-workitems report # Generate Markdown status report
```

**MCP Live ADO Access:** The `@azure-devops/mcp` server gives agents live read/write access to your ADO board directly from Copilot chat. VS Code will prompt for your ADO org name and PAT on first use.

---

## ⚙️ GitHub Actions

| Workflow | Trigger | What It Does |
|---|---|---|
| `ai-pr-review.yml` | PR opened / updated | Fetches diff → calls PR Review agent → posts AI findings as PR comment |
| `chatops-ai.yml` | `/ai <command>` in issue comment | Routes ChatOps commands to the correct agent endpoint |
| `release-notes.yml` | Push to `v*` tag | Generates AI release notes from commit history |
| `add-to-project.yml` | Issue or PR opened/labeled | Auto-adds to the **Hackathon** GitHub Project board |
| `ado-sync.yml` *(TODO)* | PR merged with `AB#ID` | Updates ADO work item state to Closed |
| `ado-triage.yml` *(TODO)* | Issue opened | AI classifies → creates ADO work item → posts ADO URL |

### ChatOps Commands

Post a comment on any issue or PR:

```
/ai review        → trigger PR diff review
/ai triage        → re-classify this issue
/ai standup       → generate standup summary from open items
```

---

## 📋 ADO Board Management

The `ado_backlog_pipeline/` bundle is a **local-first ADO management pipeline** operated by Copilot agents:

```
┌──────────────┐    pull-ado-workitems.py     ┌────────────┐
│   Azure DevOps│ ──────────────────────────► │ backlog.csv│
│   Boards      │                              │  (43 cols) │
│              │ ◄────────────────────────── │            │
└──────────────┘    sync-ado-workitems.py     └─────┬──────┘
                    (rows where _row_dirty=1)        │
                                              Copilot edits
                                              _row_dirty=1
```

**Daily workflow:**
1. Say `"sync my work notes"` → Copilot drafts Work Notes + CSV updates
2. Review the diff in `backlog.csv`
3. Set `_row_dirty=1` on rows to push → Copilot runs `sync-ado-workitems.py`
4. Commit with `AB#<ID>` → `commit-ado-sync.py` auto-updates ADO state

---

## 🔑 Commit Convention

Tag all commits linking to ADO work items:
```
git commit -m "feat: implement PR review agent AB#42"
git commit -m "fix: handle empty diff edge case Closes AB#43"
```

Keywords `Fixes`, `Closes`, `Resolves` before `AB#ID` auto-transition the work item to **Closed** via the Azure Boards GitHub App.

---

## 👥 Team

| Name | GitHub | Role |
|---|---|---|
| **Hans Havlik** | [@Hams-Ollo](https://github.com/Hams-Ollo) | ADO Pipeline, Architecture |
| **Jamil Al Bouhairi** | — | Agent Development |
| **Ricardo Reyes-Jimenez** | — | GitHub Actions, Infrastructure |
| **Uma Bharti** | — | RAG, Prompt Engineering |

**Organization:** [Terraformers-Anonymous](https://github.com/Terraformers-Anonymous)

---

## 📜 License

[MIT](LICENSE) © 2026 Terraformers Anonymous

