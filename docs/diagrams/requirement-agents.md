
# Requirement Diagram: Agents

```mermaid
requirementDiagram
  requirement sec { id: SEC-1 text: "No secrets in prompts" risk: high verifymethod: test }
  requirement perf { id: PERF-1 text: "P95 < 10s per action" risk: medium verifymethod: analysis }
  requirement qual { id: QUAL-1 text: "Detect critical issues" risk: high verifymethod: demo }
  element PR_Agent
  element Triage_Agent
  PR_Agent - satisfies -> sec
  PR_Agent - satisfies -> qual
  Triage_Agent - satisfies -> perf
```
