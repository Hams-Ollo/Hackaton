# ADO Update-Only Work Item Prompt

Use this prompt when you need GitHub Copilot to help you **write a targeted update** for an existing work item in ADO — typically end-of-day or after completing a sprint task.

> **Note:** If `WORK_NOTES.md ## Active Session` contains notes tagged with the relevant `**ADO#ID**`, use that content as the primary input source for the work notes draft. Do not ask the user to repeat information already written there.

---

## Writable fields you can update in the CSV

| Column | Notes |
|---|---|
| `Title` | |
| `State (ADO)` | New / Active / Resolved / Closed |
| `Priority` | 1=Critical 2=High 3=Medium 4=Low |
| `Risk` | Epic/Feature/Story: 1-High 2-Medium 3-Low |
| `Severity` | Bug only: 1-Critical 2-High 3-Medium 4-Low |
| `Blocked` | Bug/Task: Yes / No |
| `Story Points` | User Story / Task (Fibonacci) |
| `Effort` | Epic / Feature (Fibonacci) |
| `Business Value` | 1–500 |
| `Time Criticality` | 1–20 |
| `Start (MM/DD/YYYY)` | MM/DD/YYYY |
| `End (MM/DD/YYYY)` | MM/DD/YYYY |
| `Assigned To (ADO)` | Display name from assignee_map |
| `Tags` | Semicolon-separated |
| `Description` | Full plain-text description |
| `Work Notes` | Posted to ADO Discussion on push, then cleared |
| `Comments` | Appended to Description on push |
| `Blocker/Dependency` | Appended to Description on push |
| `Branch Name` | Creates ArtifactLink Branch relation |
| `Branch Repo` | backend / frontend / selfheal |
| `In scope for DEMO or MVP Release?` | YES / NO / TBD |
| `_row_dirty` | Set to `1` to flag row for push (auto-cleared by sync) |

**Do NOT edit:** `Backlog Priority`, `Reason`, `Board Column`, `Board Lane`, any `(ADO)` date columns, `Comment Count`, `Related Link Count`, `Last Synced (ADO)`.

---

## Prompt (copy into Copilot Chat)

```
Help me write a clean, professional update for an existing Azure DevOps work item.

Work item details:
---
ID (ADO): <e.g. 1579>
Type: <Epic / Feature / User Story / Task / Bug>
Title: <work item title>
Current State: <New / Active / Resolved>
Current Sprint: <Iteration number>
---

What I completed today / this session:
<Describe what you actually did — be specific about files, functions, APIs, or tests.>

Any blockers or dependencies:
<List blockers if any, or write "None">

New state (if changing):
<New / Active / Resolved / Closed — or "no change">

Should Blocked be set? (Bug/Task only):
<Yes / No / no change>

Was this related to a git commit? Include commit hash(es) if known:
<e.g. ab12cd3, fe45678 — or "no commit yet">

---

Output I need:
1. A concise Work Notes comment (3–5 sentences, past tense) suitable for the ADO work item history.
2. The exact CSV column values to update — formatted as "Column: Value" lines.
   Include only columns that actually change. Also include "_row_dirty: 1".
3. Any recommended state change and the reason for it.
4. If this is a Bug: recommend Severity value. If Epic/Feature/Story: recommend Risk value.

Work Notes should:
- Be written in professional past tense
- Reference specific deliverables (function names, endpoints, test cases)
- Avoid vague phrases like "worked on" or "made progress"
- End with: Ref: <commit hashes or "no commit">
```

---

## How to use the output

1. Paste the generated **Work Notes** into the `Work Notes` column of your CSV row.
2. Apply any recommended field changes (`State (ADO)`, `Blocked`, `Severity`, `Risk`, etc.) to the same row.
3. Set `_row_dirty` to `1` in the row.
4. Run `sync-ado-workitems.py` to push the update to Azure DevOps.
5. The script will post `Work Notes` to ADO as a comment, clear the cell, and clear `_row_dirty` automatically.

---

## Quick daily update command

If you just want to log a quick note without creating a full update, use:

```bash
python ado_backlog_pipeline/scripts/add-ado-comment.py
```

You'll be prompted for the work item ID, your comment text, and an optional new state.
