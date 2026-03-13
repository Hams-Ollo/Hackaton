# Commit Message Prompt — ADO Integration Convention

Use this prompt with GitHub Copilot to generate **well-structured commit messages** that automatically link to Azure DevOps work items and trigger the ADO sync pipeline.

---

## Prompt (copy into Copilot Chat)

```
Help me write a Conventional Commits-compliant git commit message for the following change.
The commit must include at least one Azure DevOps AB#ID reference so it links to the work item automatically.

Change summary:
---
Work item ID(s): <AB#1579, AB#1580, etc. — include all related items>
Work item type: <Epic / Feature / User Story / Task>
Change type: <feat | fix | refactor | docs | test | chore | ci | perf>
Scope: <module or area changed, e.g. "search-service", "pipeline", "frontend">
What changed: <brief plain-English description of what you changed>
Does this complete / close the work item? <YES / NO>
Breaking change? <YES / NO>
---

Commit message rules:
1. Format: <type>(<scope>): <short description>  [max 72 chars for subject line]
2. Subject line must be in imperative mood: "add", "fix", "update" — not "added" or "adding"
3. Include AB#<ID> at the end of the subject line or in the body for each work item
4. If this completes the item: use "fixes AB#<ID>" or "closes AB#<ID>" (triggers auto-state change)
5. Body (optional): explain WHY, not what — keep it under 100 chars per line
6. Footer (optional): list breaking changes and co-authors

Example output format:
feat(search-service): add vector similarity threshold filter AB#1579

Replaces hard-coded cosine threshold with configurable env var VECTOR_THRESHOLD.
Default value matches previous behaviour to avoid breaking existing queries.

fixes AB#1579
Co-authored-by: Jane Dev <jane@example.com>
```

---

## Quick Reference — AB# Linking Keywords

| Keyword | Effect in ADO |
|---------|---------------|
| `AB#1234` | Links commit to work item (no state change) |
| `fixes AB#1234` | Links + recommends Closed state |
| `closes AB#1234` | Links + recommends Closed state |
| `resolves AB#1234` | Links + recommends Closed state |

> **Note:** State transitions happen via `commit-ado-sync.py` (post-push hook or manual run).
> Native ADO commit linking displays the commit in the work item Development section automatically
> when `AB#ID` appears anywhere in the message.

---

## Cascade Behaviour

When `commit-ado-sync.py` runs after a push:

1. Any `fixes|closes|resolves AB#ID` → marks that item **Closed**
2. If **all child Tasks** of a User Story are Closed → User Story auto-closes
3. If **all User Stories** under a Feature are Closed → Feature auto-closes

To disable cascade for a push: `python commit-ado-sync.py --no-cascade`

---

## PowerShell Aliases (after running install-git-hooks.py)

```powershell
ado-pull       # pull latest ADO state → CSV
ado-sync       # push CSV field changes to ADO (sync-ado-workitems.py)
ado-sync-dry   # preview CSV push, no writes
ado-report     # generate Markdown status report
# Note: commit-ado-sync.py runs automatically via the post-push git hook on every git push
```
