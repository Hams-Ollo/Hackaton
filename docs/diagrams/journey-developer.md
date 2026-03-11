
# User Journey: Developer Experience

```mermaid
journey
  title Developer Journey with Agents
  section Coding
    Draft code: 3:Dev
    Open PR: 4:Dev
  section Review
    AI review posted: 5:Dev,Reviewer
    Address feedback: 3:Dev
  section Tests
    /ai tests command: 4:Dev
    Run CI: 3:Dev
  section Merge & Release
    Merge PR: 5:Dev,Maintainer
    Release notes draft: 4:Maintainer
```
