# WORK_NOTES — Developer Session Log

## How to Use This File

- **`## Active Session`** — Write notes here during the current work session. Tag specific ADO work items with `**ADO#<ID>**` (e.g., `**ADO#1579**`) so Copilot can match notes to CSV rows.
- **`## Archive`** — Completed session notes are moved here under dated sub-sections when you say *"archive my session notes"*.

### Trigger Phrases for Copilot
| What you say | What Copilot does |
|---|---|
| `"sync my work notes"` or `"update ADO from my notes"` | Reads `## Active Session` + `TODO.md ## Sprint` and drafts Work Notes text for each **ADO#ID** + new CSV rows for untracked TODOs |
| `"archive my session notes"` | Moves `## Active Session` content to a new dated sub-section under `## Archive` and clears the Active Session section |

### Tagging Syntax
- Reference a work item: `**ADO#1579**` — inline anywhere in your notes
- Multiple items in one note block: start the block with `**ADO#1579, ADO#1580**`
- New work not yet in ADO: just describe it freely — Copilot will flag it as needing a new CSV row

---

## Active Session

_Nothing logged yet  start writing your session notes here._

---

## Archive

### 2026-03-13  Migrated from ADM-Agentic/GADM to hackathon repo
- Initialized hackathon repo with ADO pipeline migrated from ADM-Agentic project (GADM)
- Cleaned all GADM/ADM-Agentic references: config, scripts, agents, data files
- Wired @azure-devops/mcp v2.4.0 into .vscode/mcp.json for VS Code Copilot agent mode
- Updated 
equirements.txt: added azure-devops, msrest, pyyaml, python-dotenv, azure-ai-projects, azure-monitor-opentelemetry
- Generalized do-config.yaml: org/project  hackathon placeholders, Sprint 1-3 iterations, all 4 team members in assignee_map, backlog.csv filename
- Reset sprint backlog in data/TODO.md for hackathon work items
- Rewrote .github/copilot-instructions.md, Codebase Review.agent.md for hackathon context


### 2026-02-27 — Recommendation Engine Fix Pass

#### Summary
Full end-to-end fix pass on the **Recommendation Engine** pipeline (`INCIDENT_RESOLUTION` intent).
Covered intent routing, synthesis output quality, field display, GroupChat reliability, ServiceNow API
integration, and terminal logging noise.

---

## Fix Round 1 — Synthesis prompt redesign

**File:** `gadm/promptlib/prompt.py`  
**Method:** `synthesis_agent_instructions()`

- Completely rewrote the synthesis prompt template.
- Pre-built the **Recommended Actions table**, **Ticket Overview**, and **Similar Incidents** sections deterministically in Python before LLM call.
- `PRIORITY_ONLY` / `ASSIGNMENT_GROUP_ONLY` → structured 5-field card with verbatim output instruction.
- `FULL_RECOMMENDATION` → pre-built sections + LLM generates Resolution Steps from conversation history only.

---

## Fix Round 2 — Intent router improvements + Pass 2 extraction hardening

**File:** `gadm/workflows/servicenow_chat_workflow.py`  
**Method:** `_deterministic_route()`

- Expanded keyword patterns for all 3 sub-intents.
- Added compound verb detection: message containing `"recommend"` + `"priority"` → `PRIORITY_ONLY`.
- `FULL_RECOMMENDATION` now catches `"recommend"`, `"recommendation"`, `"help me fix"`, `"what should I do"`, etc.
- `INCIDENT_TRIAGE` only fires when no recommendation verb is present.

**File:** `gadm/workflows/recommendation_engine.py`  
- Pass 2 extraction: changed filter from `role == "assistant"` to skip by `author_name contains "orchestrator"` — more reliable across MAF versions.

---

## Fix Round 3 — "No change" messaging + priority normalisation

**File:** `gadm/promptlib/prompt.py`

- Added `_priority_key()` helper to normalise `"3"` vs `"3 - Moderate"` before comparison.
- `priority_changed` flag now uses key comparison, not raw string equality.
- Priority analysis block always emitted for both change and no-change cases.
- Action labels updated:
  - No change → `✓ No change — keep **3 - Moderate**`
  - Change → `▲ Change to **X**`

---

## Fix Round 4 — Remove bracket annotations from output

**File:** `gadm/promptlib/prompt.py`

- Removed `[PRE-BUILT — output verbatim]` and `[GENERATE from ResolutionAgent output]` from heading strings — LLM was copying them literally into the final response.
- Moved all directives into instruction preamble prose only; headings are now clean markdown.

---

## Fix Round 5 — Field display fixes

**Files:** `gadm/workflows/recommendation_engine.py`, `gadm/promptlib/prompt.py`

| Issue | Fix |
|---|---|
| `Current Priority: 3` (missing label) | Added `_PRIORITY_LABELS` dict mapping `"1"`–`"5"` to full label strings in `_build_task_payload()` |
| `Resolved By: None` | `s.get('resolved_by', None) or '—'` in prompt template |
| `— Unknown — due Not set` (double dash in SLA) | `sla_symbol = ""` for unknown state; cell built with `.strip()` |
| `Dependencies: None mentioned.` | Instruction now says "DO NOT include this section at all" |
| `_ref()` helper | New function in `_build_task_payload()` — prefers `display_value` over `value` when unwrapping ServiceNow reference dicts |

---

## Fix Round 6 — Root cause fix: GroupChat unreliable → pure Python synthesis

**File:** `gadm/workflows/recommendation_engine.py`

- **Root cause:** GroupChat agent ordering was non-deterministic; `AssignmentGroupAgent` output was being returned instead of `SynthesisAgent` output.
- **Fix:** Added `_build_synthesis_output(task_payload)` — a pure Python method that replaces GroupChat for Phase 5.
  - Handles all 4 intents: `FULL_RECOMMENDATION`, `RESOLUTION_ONLY`, `PRIORITY_ONLY`, `ASSIGNMENT_GROUP_ONLY`.
  - Sources `resolution_text` from `resolution_context.resolution_text` (Phase 1 LLM output).
  - Embeds all pre-computed Phase 1–3 data directly into the final document.
- Phase 5 in `_run_internal()` changed from `await self._run_group_chat(...)` to `self._build_synthesis_output(task_payload)`.
- GroupChat code retained but no longer in critical path.

---

## Fix Round 7 — ServiceNow reference fields → human-readable names

**File:** `gadm/services/servicenow_read_client.py`

- Added `sysparm_display_value=all` parameter to both API methods:
  - `get_incident_by_sys_id` — `params={"sysparm_display_value": "all"}`
  - `get_incident_by_number` — `"sysparm_display_value": "all"` added to params dict
- With this parameter ServiceNow returns reference fields as `{"display_value": "SAP App Order Mgmt Run", "value": "0cfec40c..."}` instead of plain sys_id strings.
- `_ref()` helper in `_build_task_payload()` unwraps these dicts preferring `display_value`.

---

## Fix Round 8 — Health check terminal noise

**Files:** `gadm/main.py`, `gadm/dev_ui/chat_ui_v4.html`

**Problem:** The dev UI was polling `/api/diagnostics/health` every 30 seconds, flooding the uvicorn terminal with identical `200 OK` lines.

**Fix 1 — Server-side filter (`gadm/main.py`):**
- Added `_HealthCheckFilter(logging.Filter)` class that drops any `uvicorn.access` log record whose message contains `/api/diagnostics/health`.
- Attached at import time via `logging.getLogger("uvicorn.access").addFilter(_HealthCheckFilter())`.
- Health checks are still served normally — only the log line is suppressed.

**Fix 2 — Frontend poll interval (`gadm/dev_ui/chat_ui_v4.html`):**
- Changed `setInterval(checkHealth, 30_000)` → `setInterval(checkHealth, 300_000)` (30 s → 5 min).
- The status dot still updates immediately on page load and on manual "Ping" / "Health" button clicks.

---

## Files Modified Today

| File | Change |
|---|---|
| `gadm/promptlib/prompt.py` | Synthesis prompt rewrite; `_priority_key()`; bracket annotation removal; priority no-change block; SLA/resolved-by/dependencies display fixes |
| `gadm/workflows/recommendation_engine.py` | `_build_synthesis_output()` (new); `_ref()` helper; `_PRIORITY_LABELS`; Phase 5 → pure Python; Pass 2 extraction hardening |
| `gadm/workflows/servicenow_chat_workflow.py` | `_deterministic_route()` — expanded keyword matching; compound verb detection |
| `gadm/services/servicenow_read_client.py` | `sysparm_display_value=all` on both fetch methods |
| `gadm/main.py` | `_HealthCheckFilter` added; attached to `uvicorn.access` logger |
| `gadm/dev_ui/chat_ui_v4.html` | Health poll interval 30 s → 5 min |
