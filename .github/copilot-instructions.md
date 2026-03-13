# Hackathon: Agentic DevOps Automation — Copilot Instructions

## Project Overview
This is the **Terraformers Anonymous** hackathon project for the Microsoft Global Partner Hackathon (Capgemini team: Hans Havlik, Jamil Al Bouhairi, Ricardo Reyes-Jimenez, Uma Bharti).

**Use case:** Agentic AI that eliminates repetitive developer and IT ops tasks — automated PR reviews, issue triage, ADO board management, log analysis, and ChatOps — integrated across GitHub and Azure DevOps using VS Code Copilot agents, GitHub Actions, and Azure OpenAI.

## Repository Structure
```
src/agents/              # AI agent HTTP endpoints (Flask, one per agent)
  pr_review/main.py      # PR Review agent — reviews diffs, posts findings, gates CI
  issue_triage/main.py   # Issue Triage agent — classifies GitHub issues, creates ADO items
  log_analyst/main.py    # Log Analyst agent — analyzes KQL/Azure Monitor output
  test_generator/main.py # Test Generator agent — generates unit tests for changed code
  release_notes/main.py  # Release Notes agent — summarizes commits since last tag
.github/workflows/       # GitHub Actions CI/CD and automation triggers
  ai-pr-review.yml       # Triggers on PR open/sync — calls PR Review agent, gates merge
  chatops-ai.yml         # Triggers on /ai comments — routes ChatOps commands
  release-notes.yml      # Triggers on v* tags — calls Release Notes agent
  ado-sync.yml           # Triggers on PR open/merge — updates ADO work item state (TODO)
  ado-triage.yml         # Triggers on issue open — AI classify → create ADO item (TODO)
.github/scripts/         # Orchestration scripts called by workflows
  call_pr_review.py      # Fetches diff, calls agent, posts PR comment, fails CI on errors
  chatops_router.py      # Parses /ai commands and routes to agent endpoints
ado_backlog_pipeline/    # Copilot-native ADO board management bundle
  scripts/               # Python scripts: pull, sync, commit-sync, report, comment, set-priority
  config/ado-config.yaml # Single source of truth: org, project, fields, state maps, iteration map
  data/backlog.csv        # Canonical 43-column CSV — push gate for ADO changes
  data/TODO.md           # Sprint planning scratchpad (Copilot memory)
  data/WORK_NOTES.md     # Session work log (Copilot memory — tag items with **ADO#ID**)
  prompts/               # Copilot prompt files for session sync, work item creation, updates
rag/ingest/ingest_kb.py  # Azure AI Search indexer — chunks docs, generates embeddings, upserts
prompts/                 # System/user prompts for each agent (sentence-level, no inline prompts)
infra/bicep/main.bicep   # IaC for Azure OpenAI, AI Search, Key Vault, App Insights
```

## Tech Stack
- **Language:** Python 3.11
- **Agent HTTP servers:** Flask (one Azure Function / Container App per agent)
- **AI SDK:** `azure-ai-projects >= 2.0.0` (Microsoft Foundry Agent Service) or direct `azure-openai >= 1.66.0`
- **ADO SDK:** `azure-devops >= 7.0.0` + `msrest >= 0.7.1`
- **RAG:** `azure-search-documents >= 11.6.0` (HNSW vector + semantic hybrid)
- **Config:** `pyyaml >= 6.0`, `python-dotenv >= 1.0.0`
- **Observability:** `azure-monitor-opentelemetry >= 1.6.0` + Application Insights
- **CI:** GitHub Actions (`actions/checkout@v4`, `actions/setup-python@v5` with Python 3.11)
- **Auth:** `azure-identity` `DefaultAzureCredential` for Azure services; `ADO_PAT` env var for ADO SDK

## Two-Tier Architecture
**Tier 1 — VS Code Copilot Agents (developer-interactive):**
- `ADO Planner` and `ADO Executor` custom agents (`.github/agents/`) manage sprint boards conversationally
- `ado-workitems` skill (`.github/skills/`) is the workflow contract for all board operations
- ADO MCP server (`@azure-devops/mcp`) provides live ADO tool access in Copilot Agent Mode
- `ado_backlog_pipeline/` scripts handle batch pull/sync/report operations

**Tier 2 — GitHub Actions (event-driven automation):**
- PR events → PR Review agent → AI findings posted as PR comments + merge gate
- Issue open → AI triage → ADO work item created + issue comment with ADO URL
- PR merge with `AB#ID` → ADO work item state updated to `Closed`
- `/ai` comment commands → ChatOps router → appropriate agent endpoint

## ADO Pipeline — Copilot Memory System
Copilot reads these files as session memory. Keep them updated.
- `ado_backlog_pipeline/data/WORK_NOTES.md` — write session notes here, tag with `**ADO#ID**`
- `ado_backlog_pipeline/data/TODO.md` — sprint planning, items without `ADO#ID` become new board items
- Say **"sync my work notes"** → Copilot drafts Work Notes + CSV updates for each tagged item
- Say **"archive my session notes"** → moves Active Session to Archive, resets for next session

## Commit Convention
- Tag commits with `AB#<ADO-work-item-ID>` — the Azure Boards GitHub App auto-links them
- Use closing keywords to auto-transition state: `Fixes AB#123`, `Closes AB#123`, `Resolves AB#123`
- The `commit-ado-sync.py` post-push hook also handles state transitions and cascade-closes parents

## Coding Conventions
- Keep all agent prompts in `prompts/` files — no inline f-string prompts in agent Python files
- All Azure OpenAI calls must use `response_format` structured JSON output — no free-text parsing
- Use `os.getenv()` for all credentials; never hardcode keys or PATs in Python files
- Secrets live in `ado_backlog_pipeline/.env` (gitignored) and GitHub Actions repo secrets
- `ado-config.yaml` is the single source of truth for org, project, field mappings, and assignees — never hardcode ADO field names in scripts
- Set `_row_dirty=1` on any CSV row that needs to be pushed to ADO; scripts skip clean rows
- Never PATCH read-only ADO fields (see `read_only_ado_columns` in `ado-config.yaml`)
- Run all pipeline scripts from the repository root so relative paths resolve correctly
