# Hackaton — Build Tracker

> **Team:** Terraformers Anonymous — Hans Havlik, Jamil Al Bouhairi, Ricardo Reyes-Jimenez, Uma Bharti  
> **Challenge:** Agentic DevOps Automation — Microsoft Global Partner Hackathon  
> **Repo:** [RARJ-CAP/Hackaton](https://github.com/RARJ-CAP/Hackaton)

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
  - `AZURE_SEARCH_KEY` — Azure AI Search admin key
  - `AZURE_SEARCH_ENDPOINT` — Azure AI Search endpoint URL
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
