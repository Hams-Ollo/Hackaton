---
name: ADO Backlog Pipeline Rules
description: Rules for editing or operating the local ADO backlog pipeline, including CSV, TODO, WORK_NOTES, config, prompts, and scripts.
applyTo: ado_backlog_pipeline/**
---

# ADO Backlog Pipeline Rules

- Keep `ado_backlog_pipeline/` as an operational bundle outside `.github/skills/`.
- Prefer configuration changes in `config/ado-config.yaml` over hardcoded behavior in scripts.
- Preserve repo-root relative paths in documentation, prompts, and script examples.
- Treat `data/ado_azure_ai_search_work_items.csv` as the push gate for ADO changes.
- Maintain the contract between `TODO.md`, `WORK_NOTES.md`, and the canonical CSV.
- Do not assume the shared board snapshot and the personal `work-log.csv` serve the same purpose.
- Keep credentials out of committed files and use `ado_backlog_pipeline/.env` for PAT-based local auth.
