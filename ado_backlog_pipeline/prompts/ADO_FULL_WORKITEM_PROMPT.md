# ADO Full Work Item CSV Prompt

Use this prompt when asking GitHub Copilot to help you **fill out or review a full work item row** in the backlog CSV before syncing to Azure DevOps.

> **Note:** If `TODO.md ## Sprint / This Week` contains items with no `ADO#ID`, use those items as the source for title, description, type, and priority when drafting new CSV rows.

---

## Column Reference (43 columns)

### Group: Identity
| Column | ADO Field | Writable | Notes |
|---|---|---|---|
| `ID (ADO)` | System.Id | No | Leave blank for new items — sync script fills it |
| `Type` | System.WorkItemType | No | Epic / Feature / User Story / Task / Bug |
| `Parent ID (ADO)` | System.Parent | Yes | ADO ID of parent item |
| `Title` | System.Title | Yes | |
| `Area Path` | System.AreaPath | Yes | |
| `Iteration #` | System.IterationPath | Yes | Use shorthand: 9, 10, 11 |

### Group: Planning
| Column | ADO Field | Writable | Notes |
|---|---|---|---|
| `Priority` | Microsoft.VSTS.Common.Priority | Yes | 1=Critical 2=High 3=Medium 4=Low |
| `Backlog Priority` | Microsoft.VSTS.Common.BacklogPriority | **Read-only** | System-managed ordering — do not edit |
| `Story Points` | Microsoft.VSTS.Scheduling.StoryPoints | Yes | User Story / Task only. Fibonacci: 1,2,3,5,8,13,20 |
| `Effort` | Microsoft.VSTS.Scheduling.Effort | Yes | Epic / Feature only. Fibonacci: 1,2,3,5,8,13,20 |
| `Business Value` | Microsoft.VSTS.Common.BusinessValue | Yes | 1–500 |
| `Time Criticality` | Microsoft.VSTS.Common.TimeCriticality | Yes | 1–20 (higher = more time-sensitive) |
| `Risk` | Microsoft.VSTS.Common.Risk | Yes | Epic / Feature / User Story. 1-High 2-Medium 3-Low |
| `Severity` | Microsoft.VSTS.Common.Severity | Yes | Bug only. 1-Critical 2-High 3-Medium 4-Low |

### Group: Scheduling
| Column | ADO Field | Writable | Notes |
|---|---|---|---|
| `Start (MM/DD/YYYY)` | Microsoft.VSTS.Scheduling.StartDate | Yes | MM/DD/YYYY |
| `End (MM/DD/YYYY)` | Microsoft.VSTS.Scheduling.TargetDate | Yes | MM/DD/YYYY |

### Group: State & Board
| Column | ADO Field | Writable | Notes |
|---|---|---|---|
| `State (ADO)` | System.State | Yes | New / Active / Resolved / Closed |
| `Reason` | System.Reason | **Read-only** | Set by ADO workflow transitions |
| `Blocked` | Microsoft.VSTS.CMMI.Blocked | Yes | Bug / Task. Yes / No |
| `Board Column` | System.BoardColumn | **Read-only** | Set by board drag-and-drop |
| `Board Lane` | System.BoardLane | **Read-only** | Set by board swimlane |

### Group: Audit Dates (all read-only — populated by pull)
| Column | ADO Field |
|---|---|
| `Created Date (ADO)` | System.CreatedDate |
| `Changed Date (ADO)` | System.ChangedDate |
| `State Changed Date (ADO)` | Microsoft.VSTS.Common.StateChangeDate |
| `Activated Date (ADO)` | Microsoft.VSTS.Common.ActivatedDate |
| `Resolved Date (ADO)` | Microsoft.VSTS.Common.ResolvedDate |
| `Closed Date (ADO)` | Microsoft.VSTS.Common.ClosedDate |

### Group: Assignment & Tags
| Column | ADO Field | Writable |
|---|---|---|
| `Assigned To (ADO)` | System.AssignedTo | Yes |
| `Tags` | System.Tags | Yes |

### Group: Counts (read-only — populated by pull)
| Column | ADO Field |
|---|---|
| `Comment Count` | System.CommentCount |
| `Related Link Count` | System.RelatedLinkCount |

### Group: Content
| Column | ADO Field | Writable |
|---|---|---|
| `Description` | System.Description | Yes |

### Group: Local-only (never synced from ADO — preserve these manually)
| Column | Notes |
|---|---|
| `Status` | Derived Active/Closed — local only |
| `Owner` | Local team ownership label |
| `Dev Lead` | Local dev lead label |
| `Work Notes` | Intraday scratchpad — posted to ADO Discussion on push, then cleared |
| `Comments` | Appended to Description on push |
| `Blocker/Dependency` | Appended to Description on push |
| `Branch Name` | Creates ArtifactLink Branch relation on push |
| `Branch Repo` | backend / frontend / selfheal |
| `In scope for DEMO or MVP Release?` | YES / NO / TBD — adds `mvp-scope` tag on push |

### Group: Meta
| Column | Notes |
|---|---|
| `Last Synced (ADO)` | UTC timestamp set by pull-ado-workitems.py — do not edit |
| `_row_dirty` | Set to `1` to flag row has unpushed local edits; cleared automatically by sync |

---

## Prompt (copy into Copilot Chat)

```
I have an Azure DevOps work item I need to add or update in my CSV backlog.
Please help me fill out all required fields for a complete, high-quality entry.

The CSV has 43 canonical columns in these groups:
Identity: ID (ADO), Type, Parent ID (ADO), Title, Area Path, Iteration #
Planning: Priority, Backlog Priority*, Story Points, Effort, Business Value, Time Criticality, Risk, Severity
Scheduling: Start (MM/DD/YYYY), End (MM/DD/YYYY)
State & Board: State (ADO), Reason*, Blocked, Board Column*, Board Lane*
Audit Dates*: Created Date (ADO), Changed Date (ADO), State Changed Date (ADO), Activated Date (ADO), Resolved Date (ADO), Closed Date (ADO)
Assignment & Tags: Assigned To (ADO), Tags
Counts*: Comment Count, Related Link Count
Content: Description
Local-only: Status, Owner, Dev Lead, Work Notes, Comments, Blocker/Dependency, Branch Name, Branch Repo, In scope for DEMO or MVP Release?
Meta: Last Synced (ADO)*, _row_dirty*
(* = read-only or system-managed — leave blank)

Context about this work item:
---
Work item type: <Epic / Feature / User Story / Task / Bug>
Title: <your title here>
Description summary: <brief description>
Parent item: <parent ID or title if known>
Sprint / iteration: <e.g. "10" or "Iteration 10">
Assigned to: <name or alias>
Branch: <branch name if applicable>
Repo: <backend / frontend / selfheal>
---

Rules:
- Priority: 1 (Critical) / 2 (High) / 3 (Medium) / 4 (Low)
- Risk (Epic/Feature/Story): 1-High / 2-Medium / 3-Low
- Severity (Bug only): 1-Critical / 2-High / 3-Medium / 4-Low
- Blocked (Bug/Task): Yes / No
- Effort (Epic/Feature only): Fibonacci — 1, 2, 3, 5, 8, 13, 20
- Story Points (User Story/Task only): Fibonacci — 1, 2, 3, 5, 8, 13, 20
- Business Value: 1–500 (higher = more customer value)
- Time Criticality: 1–20 (higher = more time-sensitive)
- State (ADO): New | Active | Resolved | Closed
- Start / End: MM/DD/YYYY format
- In scope for DEMO or MVP Release?: YES | NO | TBD
- Branch Repo: backend | frontend | selfheal (leave blank if no branch yet)
- Leave ALL read-only and audit date columns blank — pull script fills them

Please output a single CSV row I can paste directly into my backlog file.
```

---

## Tips

- Leave `ID (ADO)` blank for new items — the sync script will populate it after creation.
- Set `_row_dirty` to `1` after manually editing a row to flag it for push. The sync script clears it automatically after a successful update.
- `Work Notes` is your intraday scratchpad. Write free-form notes here; they are posted to ADO as a comment when you run `sync-ado-workitems.py`, then cleared automatically.
- Audit date columns (`Created Date (ADO)`, `State Changed Date (ADO)`, etc.) are populated automatically on pull — use them for querying stale items or tracking cycle time.
- `Last Synced (ADO)` is managed by `pull-ado-workitems.py` — do not edit manually.
- Run `pull-ado-workitems.py` after adding a new row to confirm the item was created and populate all read-only fields.
