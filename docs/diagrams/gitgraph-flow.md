
# Git Graph: Branch Strategy (Example)

```mermaid
gitGraph
  commit id:"init"
  branch feature/agent
  checkout feature/agent
  commit id:"work1"
  commit id:"work2"
  checkout main
  commit id:"hotfix"
  merge feature/agent
  tag "v0.1"
```
