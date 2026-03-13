# TODO — Sprint Planning Scratchpad

## How to Use This File

This is the **developer sprint planning board**. Copilot reads this file when you ask to *"sync my work notes"* or *"create ADO work items from my TODOs"* to draft new CSV rows for items that have no `ADO#ID` yet.

### Item Syntax
```
- [ ] <Title/description of work>  |  Type: <Epic|Feature|User Story|Task>  |  Priority: <1-4>  |  ADO#<ID if known>
```

- Leave `ADO#ID` blank for items not yet in ADO — Copilot will flag them for new CSV row creation.
- Use `- [x]` to mark done. Move completed items to `## Done` at end of sprint.
- Assign iterations using `Sprint: <number>` if known.

---

## 🔴 Sprint / This Week

<!-- Active sprint items — things you are working on RIGHT NOW or this week -->
<!-- Format: - [ ] <Title>  |  Type: <type>  |  Priority: <1-4>  |  ADO#<ID> -->

### PR Review Agent
- [ ] Replace hardcoded `call_aoai()` stub with real `azure-ai-projects` SDK call in `src/agents/pr_review/main.py`  |  Type: Task  |  Priority: 1
- [ ] Wire RAG into PR review — pull relevant standards snippets from Azure AI Search before AOAI call  |  Type: Task  |  Priority: 1

### Issue Triage Agent
- [ ] Implement `src/agents/issue_triage/main.py` — Flask server `POST /triage`, label + route GitHub issues via AOAI  |  Type: Task  |  Priority: 1

### ADO Sync GitHub Action
- [ ] Build `.github/workflows/ado-sync.yml` — triggers on PR merge + manual dispatch; calls ADO pipeline scripts  |  Type: Task  |  Priority: 1
- [ ] Create `src/actions/ado_sync.py` — GitHub Action wrapper that invokes `commit-ado-sync.py` with env secrets  |  Type: Task  |  Priority: 1

### ADO Triage GitHub Action
- [ ] Build `.github/workflows/ado-triage.yml` — triggers on issue opened/labeled; calls triage + ADO create  |  Type: Task  |  Priority: 2
- [ ] Create `src/actions/ado_triage.py` — Action wrapper that calls `add-ado-comment.py` and creates ADO work items  |  Type: Task  |  Priority: 2

---

## 🟡 Backlog / Soon

<!-- Items planned for upcoming sprints or next week -->

### ChatOps
- [ ] Implement `src/agents/chatops/chatops_router.py` — routes `/ai` issue comments to correct agent  |  Type: User Story  |  Priority: 2
- [ ] Wire `.github/workflows/chatops-ai.yml` to call `chatops_router.py` with GitHub context  |  Type: Task  |  Priority: 2

### Additional Agents
- [ ] Implement `src/agents/log_analyst/main.py` — Flask server `POST /analyze-logs`, Azure Monitor log analysis  |  Type: User Story  |  Priority: 2
- [ ] Implement `src/agents/test_generator/main.py` — Flask server `POST /generate-tests`, test scaffold generation  |  Type: User Story  |  Priority: 3
- [ ] Implement `src/agents/release_notes/main.py` — Flask server `POST /release-notes`, tag-triggered changelog  |  Type: User Story  |  Priority: 2
- [ ] Wire `.github/workflows/release-notes.yml` to call release_notes agent on `v*` tags  |  Type: Task  |  Priority: 2

### Prompts & RAG
- [ ] Expand `prompts/pr_review_system.md` — full system prompt with code review criteria, AB#ID convention, severity levels  |  Type: Task  |  Priority: 1
- [ ] Expand `prompts/triage_user.md` — label taxonomy, routing rules, ADO work item type mapping  |  Type: Task  |  Priority: 1
- [ ] Expand `prompts/log_analyst_user.md` — log pattern recognition, Azure Monitor query examples  |  Type: Task  |  Priority: 2
- [ ] Expand `prompts/release_notes_user.md` — changelog template, commit grouping, Breaking Changes section  |  Type: Task  |  Priority: 2
- [ ] Fix `rag/ingest/ingest_kb.py` import bug — `OpenAIClient` → `AzureOpenAI` (line ~45)  |  Type: Task  |  Priority: 1
- [ ] Run `ingest_kb.py` against hackathon standards docs to populate AI Search index  |  Type: Task  |  Priority: 2

### Infrastructure
- [ ] Build `infra/bicep/main.bicep` — provision AOAI, AI Search, Azure Functions, Key Vault, App Insights  |  Type: Feature  |  Priority: 2
- [ ] Add GitHub Secrets: `ADO_PAT`, `ADO_ORG`, `ADO_PROJECT`, `AZURE_OPENAI_KEY`, `AZURE_OPENAI_ENDPOINT`  |  Type: Task  |  Priority: 1

### ADO Pipeline Tooling
- [ ] Confirm and update ADO org URL + project name in `ado-config.yaml` (currently placeholder RARJ-CAP)  |  Type: Task  |  Priority: 1
- [ ] Replace placeholder emails in `ado-config.yaml` `assignee_map` with real team emails  |  Type: Task  |  Priority: 1
- [ ] Run `pull-ado-workitems.py` against real ADO project to seed `backlog.csv`  |  Type: Task  |  Priority: 2
- [ ] Delete or gitignore `ado_backlog_pipeline/data/ado_azure_ai_search_work_items.csv` (GADM legacy file)  |  Type: Task  |  Priority: 2
- [ ] Build `DAILY_STANDUP_PROMPT.md` — standup summary from WORK_NOTES Active Session + In Progress CSV items  |  Type: Task  |  Priority: 3

---

## ✅ Done

<!-- Completed items — move here at end of sprint -->

- [x] Migrate ADO backlog pipeline from ADM-Agentic/GADM to hackathon repo  |  Done 2026-03-13
- [x] Rewrite `.github/copilot-instructions.md` — hackathon context, stack, agent paths, AB#ID convention  |  Done 2026-03-13
- [x] Rewrite `Codebase Review.agent.md` — hackathon stack dimensions, known issues  |  Done 2026-03-13
- [x] Generalize `ado-config.yaml` — RARJ-CAP placeholders, all 4 team members, renamed CSV  |  Done 2026-03-13
- [x] Reset `WORK_NOTES.md` — clean active session, migration archive entry  |  Done 2026-03-13
- [x] Wire `.vscode/mcp.json` — `@azure-devops/mcp` v2.4.0 with domain filter  |  Done 2026-03-13
- [x] Update `requirements.txt` — all deps with pinned versions  |  Done 2026-03-13
- [x] Remove GADM docstring/error references from all 9 pipeline scripts  |  Done 2026-03-13
