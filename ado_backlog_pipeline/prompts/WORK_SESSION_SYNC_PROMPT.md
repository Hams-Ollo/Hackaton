# Work Session Sync Prompt

Use this prompt (or the trigger phrases below) to translate session work notes and sprint TODOs into ready-to-paste CSV updates and new work item rows.

---

## Trigger Phrases

Say any of these in Copilot Chat to activate this workflow:
- `"sync my work notes"`
- `"update ADO from my notes"`
- `"prepare my ADO updates"`
- `"draft work notes from my session"`

---

## Prompt (copy into Copilot Chat, or just use the trigger phrases above)

```
I need to prepare ADO work item updates from my session notes and sprint TODOs.

Please do the following:

STEP 1 — Read context files:
- Read `ado_backlog_pipeline/data/WORK_NOTES.md` — the `## Active Session` section contains my technical session notes.
- Read `ado_backlog_pipeline/data/TODO.md` — the `## Sprint / This Week` section contains active sprint items.

STEP 2 — For each **ADO#<ID>** tag found in WORK_NOTES Active Session:
Produce:
  a) A Work Notes comment (3–5 sentences, professional past tense) suitable for the ADO work item's Discussion / History panel.
     - Reference specific files, method names, or endpoints touched.
     - Avoid vague phrases like "worked on" or "made changes".
     - End with: `Ref: <commit hashes if any, or "no commit yet">`
  b) A list of exact CSV column updates in "Column: Value" format for that row.
  c) A recommended State (ADO) change (or "no change") with reasoning.

STEP 3 — For each TODO item in TODO.md Sprint section that has NO ADO#ID:
Produce a full new CSV row using the 27-column schema from ADO_FULL_WORKITEM_PROMPT.md.
Mark `ID (ADO)` as blank (these will be created on next `ado-sync`).

STEP 4 — Output summary:
Print a summary table:
  | ADO# | Action | Work Notes (first sentence) | State Change |
  |---|---|---|---|

STEP 5 — Remind me:
  1. Paste Work Notes text into the matching CSV `Work Notes` column
  2. Apply any field changes to the CSV row
  3. Paste any new rows into the CSV (blank ID)
  4. Run `ado-sync` to push everything to Azure DevOps
  5. Say "archive my session notes" to move WORK_NOTES Active Session to Archive
```

---

## Archive Trigger

When you say **"archive my session notes"**, Copilot will:

1. Read the current `## Active Session` content from `WORK_NOTES.md`
2. Move it to a new dated sub-section under `## Archive` (format: `### YYYY-MM-DD — <brief title>`)
3. Replace `## Active Session` with `_Nothing logged yet — start writing your session notes here._`
4. Confirm the archive is complete and the file is ready for the next session

---

## Output Format Reference

### Work Notes comment (for CSV `Work Notes` column)
```
Completed <specific deliverable>. Refactored <method/class> in <file> to <outcome>.
Updated <other file> to handle <scenario>. All existing tests pass; added <N> new
test cases covering <edge case>. Ref: <commit hash or "no commit yet">
```

### CSV column update block
```
Column: Value
State (ADO): Active
Status: In Progress
Story Points: 3
End (MM/DD/YYYY): 03/07/2026
```

### New CSV row (no ADO#ID yet)
```
,User Story,,<Title>,<Description>,,,,Hans Havlik,Hans Havlik,,Active,In Progress,2,9,ADM-Agentic\ADM-Agentic Team,02/27/2026,03/14/2026,,3,200,5,adm-agentic; csv-sync,TBD,,,
```

---

## Notes

- **WORK_NOTES.md** is the source of truth for *what was actually built*. Write freely and technically — Copilot will professionalize it for ADO.
- **TODO.md** is the source of truth for *what is planned*. Use it to generate new work item rows.
- Neither file is ever auto-modified by scripts — only Copilot (on your explicit request) and you manually change them.
- The CSV `Work Notes` column is cleared by `sync-ado-workitems.py` after posting to ADO. `WORK_NOTES.md` is **not** cleared by any script — it is only archived on your trigger.
