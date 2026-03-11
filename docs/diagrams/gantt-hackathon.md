
# Gantt: 10-Day Plan

```mermaid
gantt
  dateFormat  YYYY-MM-DD
  title 10-Day Hackathon Plan
  section Setup
  Azure resources         :a1, 2026-03-11, 2d
  Repo & scaffolding      :a2, after a1, 1d
  section Core Agents
  PR Review Agent         :b1, 3d
  Test Generator          :b2, after b1, 1d
  Issue Triage            :b3, after b1, 1d
  section Ops & RAG
  Log Analyst + RAG       :c1, 3d
  section Eval & Polish
  Prompt Flow Evals       :d1, 2d
  Demo & Docs             :d2, after d1, 1d
```
