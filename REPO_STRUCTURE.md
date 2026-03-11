
# Repository Structure

```
ai-agents-hackathon/
├─ README.md
├─ requirements.txt
├─ REPO_STRUCTURE.md
├─ docs/
│  ├─ architecture.md
│  └─ diagrams/
│     ├─ system-context.md
│     ├─ sequence-pr-review.md
│     ├─ sequence-chatops.md
│     ├─ deployment-azure-github.md
│     ├─ state-issue-triage.md
│     ├─ state-incident.md
│     ├─ er-knowledge-base.md
│     ├─ class-agents.md
│     ├─ gantt-hackathon.md
│     ├─ journey-developer.md
│     ├─ timeline-release.md
│     ├─ pie-costs.md
│     ├─ gitgraph-flow.md
│     ├─ mindmap-capabilities.md
│     ├─ quadrant-priorities.md
│     └─ sankey-costflow.md
├─ prompts/
│  ├─ pr_review_system.md
│  ├─ triage_user.md
│  ├─ log_analyst_user.md
│  └─ release_notes_user.md
├─ src/
│  └─ agents/
│     ├─ pr_review/
│     │  └─ main.py
│     ├─ test_generator/
│     │  └─ main.py
│     ├─ issue_triage/
│     │  └─ main.py
│     ├─ log_analyst/
│     │  └─ main.py
│     └─ release_notes/
│        └─ main.py
├─ .github/
│  ├─ workflows/
│  │  ├─ ai-pr-review.yml
│  │  ├─ chatops-ai.yml
│  │  └─ release-notes.yml
│  └─ scripts/
│     ├─ call_pr_review.py
│     └─ chatops_router.py
├─ evals/
│  ├─ pr_reviews_eval.jsonl
│  └─ triage_eval.jsonl
├─ configs/
│  └─ settings.example.json
├─ infra/
│  └─ bicep/
│     └─ main.bicep
├─ .devcontainer/
│  └─ devcontainer.json
└─ tests/
   └─ sample_test.py
```
