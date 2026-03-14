# Hackaton — Build Tracker

> **Team:** Terraformers Anonymous — Hans Havlik, Jamil Al Bouhairi, Ricardo Reyes-Jimenez, Uma Bharti  
> **Challenge:** Agentic DevOps Automation — Microsoft Global Partner Hackathon  
> **Repo:** [Terraformers-Anonymous/hackathon-project](https://github.com/Terraformers-Anonymous/hackathon-project)

---

## 🔧 Team Setup (Do First)

These must be done before any agent can run end-to-end.

- [ ] **Confirm ADO org + project** — update `ado_backlog_pipeline/config/ado-config.yaml`:
  - `org_url: https://dev.azure.com/<YOUR_ORG>` (currently placeholder `RARJ-CAP`)
  - `project: <YOUR_PROJECT>` (currently placeholder `Hackaton`)
- [ ] **Replace placeholder emails** in `ado-config.yaml` `assignee_map` section with real team emails
- [ ] **Add GitHub Secrets** to repo settings:
  - `ADO_PAT` — Azure DevOps Personal Access Token (Work Items: Read & Write, Code: Read)
  - `ADO_ORG` — ADO org name (matches `org_url` above)
  - `ADO_PROJECT` — ADO project name
  - `AZURE_OPENAI_KEY` — Azure OpenAI API key
  - `AZURE_OPENAI_ENDPOINT` — Azure OpenAI endpoint URL
  - `AZURE_OPENAI_DEPLOYMENT` — Azure OpenAI deployment name (e.g. `gpt-4o`)
  - `AZURE_SEARCH_KEY` — Azure AI Search admin key
  - `AZURE_SEARCH_ENDPOINT` — Azure AI Search endpoint URL
  - `PROJECT_URL` — GitHub Projects v2 URL (for `add-to-project.yml`)
  - `PROJECT_TOKEN` — GitHub PAT with `project` scope (for `add-to-project.yml`)
  - `AI_PR_REVIEW_FUNC_URL` — Azure Function App base URL (for `ai-pr-review.yml`)
  - `AI_PR_REVIEW_FUNC_KEY` — Azure Function host key (for `ai-pr-review.yml`)
  - `AI_CHATOPS_FUNC_URL` — Azure Function App base URL (for `chatops-ai.yml`)
  - `AI_CHATOPS_FUNC_KEY` — Azure Function host key (for `chatops-ai.yml`)
- [ ] **Create `.env`** locally from `.env.example` (never commit):
  ```
  ADO_PAT=...
  AZURE_OPENAI_ENDPOINT=...
  AZURE_OPENAI_KEY=...
  AZURE_OPENAI_DEPLOYMENT=...
  AZURE_SEARCH_ENDPOINT=...
  AZURE_SEARCH_KEY=...
  AZURE_SEARCH_INDEX=hackathon-standards
  ```
- [ ] **Verify MCP auth** — run `npx -y @azure-devops/mcp <your-org> -d core work work-items repositories` and confirm browser OAuth completes
- [ ] **Populate `github-config.yaml` project field IDs** — in Copilot Chat (GitHub Project Manager agent): `"List all fields on project 1 for org Terraformers-Anonymous"` → copy `PVT_...` project ID and all `PVTSSF_...` field IDs + option IDs into `github_devflow/config/github-config.yaml` under `project_fields`
- [ ] **Confirm GitHub usernames** in `github_devflow/config/github-config.yaml` `assignee_map` — replace `TODO: confirm` placeholder comments with real GitHub usernames for all 4 team members
- [ ] **Seed backlog** — run `python ado_backlog_pipeline/scripts/pull-ado-workitems.py` against real ADO project; verify `ado_backlog_pipeline/data/backlog.csv` populates
- [ ] **Delete GADM legacy file** — `ado_backlog_pipeline/data/ado_azure_ai_search_work_items.csv` (or add to `.gitignore`)
- [ ] **Install Python deps** — `pip install -r requirements.txt` in project root

---

## 🏗️ Build Work — Priority 1 (Demo-critical)

### PR Review Agent — `src/agents/pr_review/main.py`
- [ ] Replace stub `call_aoai()` with real `azure-ai-projects` SDK call
  - Use `AIProjectClient` + `azure-openai` SDK with env-var config
  - Pass diff + RAG snippets as user message; `pr_review_system.md` as system prompt
- [ ] Wire RAG — query Azure AI Search for relevant standards before AOAI call
  - `standards_snippets = search_client.search(query=diff_summary, top=3)`
  - Embed snippets in prompt context
- [ ] Expand `prompts/pr_review_system.md` — full system prompt with:
  - Code review criteria (security, perf, style, AB#ID convention)
  - Severity levels (blocker/warning/suggestion)
  - Output format (structured JSON with `summary`, `issues[]`, `ab_refs[]`)

### Issue Triage Agent — `src/agents/issue_triage/main.py`
- [ ] Implement Flask server `POST /triage`
  - Parse GitHub issue title + body from request JSON
  - Call AOAI with `triage_user.md` prompt — return label + ADO work item type + assignee
  - Return `{"labels": [], "ado_type": "Bug|User Story|Task", "assignee": "..."}`
- [ ] Expand `prompts/triage_user.md` — label taxonomy, routing rules, ADO type mapping

### GitHub Actions — ADO Sync
- [ ] Build `.github/workflows/ado-sync.yml`:
  - Triggers: `pull_request` (closed + merged), `workflow_dispatch`
  - Steps: checkout → setup Python → `pip install -r requirements.txt` → run `commit-ado-sync.py`
  - Secrets: `ADO_PAT`, `ADO_ORG`, `ADO_PROJECT`
- [ ] Create `src/actions/ado_sync.py` — thin wrapper; reads `GITHUB_TOKEN`, `ADO_*` env vars, invokes pipeline script

### GitHub Actions — ADO Triage  
- [ ] Build `.github/workflows/ado-triage.yml`:
  - Trigger: `issues` (opened, labeled)
  - Steps: call `issue_triage` agent → apply GitHub labels → create ADO work item via `add-ado-comment.py` or REST
- [ ] Create `src/actions/ado_triage.py` — reads issue payload, calls triage agent, applies labels via GitHub API

### ChatOps Script — `.github/scripts/chatops_router.py`
- [ ] Implement full script (currently a single `# TODO` comment — `chatops-ai.yml` will silently fail):
  - Parse `/ai <command>` from `--comment` arg
  - Load issue context (title, body, labels) via GitHub REST
  - POST to `{AI_CHATOPS_FUNC_URL}/chatops_router` with `{command, issue_body, labels, repo, issue_number}`
  - Read JSON response `{action, labels, response_text}`
  - Post `response_text` back as GitHub issue comment via REST
  - Optionally apply returned `labels` to the issue

### Release Notes Script — `.github/scripts/call_release_notes.py`
- [ ] Create this file (currently **missing** — `release-notes.yml` crashes at runtime):
  - Accept `--repo`, `--tag`, `--github-token` args
  - Compute commit range: from previous tag to `--tag` via GitHub Releases API
  - POST commit list + PR titles to `{AZURE_OPENAI_ENDPOINT}` or Function endpoint
  - Read `release_notes_user.md` prompt; call Azure OpenAI with structured JSON schema
  - Create GitHub Release via REST API with generated notes body

---

## 🏗️ Build Work — Priority 2

### ChatOps — `.github/workflows/chatops-ai.yml`
- [ ] Implement `src/agents/chatops/chatops_router.py`:
  - Parse `/ai <command>` from issue comment body
  - Route: `/ai review` → pr_review, `/ai triage` → issue_triage, `/ai standup` → standup summary
- [ ] Wire `chatops-ai.yml` to call `chatops_router.py` with `GITHUB_TOKEN` + `GITHUB_REPOSITORY`

### Release Notes Agent — `src/agents/release_notes/main.py`
- [ ] Implement Flask server `POST /release-notes`
  - Parse git tag + commit range from request
  - Call AOAI with `release_notes_user.md` prompt — group commits by type, flag breaking changes
- [ ] Wire `release-notes.yml` to trigger on `v*` tags and call release_notes agent
- [ ] Expand `prompts/release_notes_user.md` — changelog template, commit grouping rules

### Log Analyst Agent — `src/agents/log_analyst/main.py`
- [ ] Implement Flask server `POST /analyze-logs`
  - Accept Azure Monitor log export JSON
  - Call AOAI with `log_analyst_user.md` — identify anomalies, error spikes, root cause hints
- [ ] Expand `prompts/log_analyst_user.md` — log pattern recognition, Azure Monitor Kusto examples

### RAG Knowledge Base
- [ ] Fix import bug in `rag/ingest/ingest_kb.py` — `OpenAIClient` → `AzureOpenAI` (line ~45)
- [ ] Run `ingest_kb.py` to populate Azure AI Search index (`hackathon-standards`) with:
  - Coding standards docs
  - PR review guidelines
  - ADO field reference from `ADO_FULL_WORKITEM_PROMPT.md`

---

## 🏗️ Build Work — Agent Enhancements (Demo Polish)

### Coding Agent Integration — GitHub DevOps Engineer agent
- [ ] Update `.github/agents/GitHub DevOps Engineer.agent.md` — add instructions to use the `copilot` toolset on the remote GitHub MCP server:
  - When user says "implement issue #N" or "assign issue #N to Copilot", use the `copilot` MCP toolset to assign the issue to `copilot[bot]`
  - Copilot Coding Agent then autonomously: creates `copilot/*` branch → implements fix → opens PR with "Closes #N"
  - Confirm back with the PR URL once the agent creates it
  - **Requires:** GitHub Copilot Pro/Business plan + remote GitHub MCP server (not local)

### Sprint Health Check — GitHub Project Manager agent
- [ ] Update `.github/agents/GitHub Project Manager.agent.md` — add a structured Sprint Health Check flow:
  - When user asks "what's blocking the sprint" or "sprint health check", query:
    1. All In Progress issues — check for linked PRs; flag any with no PR and >2 days since last update
    2. All Blocked issues — surface immediately
    3. All Todo issues in current sprint — check assignee; flag unassigned
    4. Open PRs awaiting review — flag stale reviews (>1 day without approval)
  - Return ranked blocker report: `🔴 Blockers | 🟡 At Risk | ✅ On Track` with issue links, assignees, and one recommended action per item

---

## 🏗️ Build Work — Priority 3

### Infrastructure as Code
- [ ] Build `infra/bicep/main.bicep`:
  - Azure OpenAI (gpt-4o deployment)
  - Azure AI Search (standard tier, HNSW index)
  - Azure Functions (Flex Consumption, Python 3.11)
  - Key Vault (store all secrets, managed identity access)
  - Application Insights (connected to all agents)
- [ ] Add `infra/bicep/parameters.bicepparam` with environment-specific values

### Test Generator Agent — `src/agents/test_generator/main.py`
- [ ] Implement Flask server `POST /generate-tests`
  - Accept source file path + function name
  - Call AOAI — generate pytest stubs with edge cases
  - Return test file content

### ADO Pipeline Enhancements
- [ ] Build `ado_backlog_pipeline/prompts/DAILY_STANDUP_PROMPT.md` — standup summary from WORK_NOTES + In Progress CSV items
- [ ] Add `ado-todo-push` script — parse TODO.md sprint items → blank-ID CSV rows ready for `ado-sync`

### Evaluation & Observability
- [ ] Create `evals/` folder with sample datasets for each agent
  - `evals/pr_review_samples.jsonl` — diff + expected review output pairs
  - `evals/triage_samples.jsonl` — issue title/body + expected label/type pairs
- [ ] Wire `azure-monitor-opentelemetry` tracing into Flask agent servers
  - Add `configure_azure_monitor(connection_string=...)` to each `main.py`
  - Trace AOAI calls + RAG queries as named spans

---

## ✅ Done

- [x] Deep research: agentic DevOps landscape — GitHub Copilot Coding Agent, GitHub MCP v0.32.0, ADO MCP v2.4.0, Azure AI Foundry, competitor analysis — 2026-03-14
- [x] Created `HACKATHON_ROADMAP.md` — full technical roadmap, 5 Mermaid architecture/workflow diagrams, component status, gap analysis, Gantt roadmap, demo script, team onboarding, key decisions for Monday — 2026-03-14
- [x] Created `hackathon-use-cases.md` — catalogue of 9 standout hackathon use cases across 6 domains for future reference — 2026-03-14
- [x] Clone Ricardo's repo + migrate Hans's ADO pipeline assets — 2026-03-13
- [x] Rewrite `.github/copilot-instructions.md` (GADM → hackathon context) — 2026-03-13
- [x] Rewrite `Codebase Review.agent.md` (hackathon stack dimensions) — 2026-03-13
- [x] Generalize `ado-config.yaml` (RARJ-CAP placeholders, full team) — 2026-03-13
- [x] Reset `WORK_NOTES.md` (clean session) — 2026-03-13
- [x] Wire `.vscode/mcp.json` (`@azure-devops/mcp` v2.4.0) — 2026-03-13
- [x] Update `requirements.txt` (all deps, pinned versions) — 2026-03-13
- [x] Remove GADM references from all 9 pipeline scripts — 2026-03-13
- [x] Add MCP operating rules to ADO Planner + Executor agents — 2026-03-13
- [x] Create `ado_backlog_pipeline/data/backlog.csv` (43-column header) — 2026-03-13
- [x] Reset `ado_backlog_pipeline/data/TODO.md` (hackathon backlog) — 2026-03-13
