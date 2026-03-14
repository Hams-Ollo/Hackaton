---
name: Platform Swap Rules
description: Rules for the platform-agnostic MCP design — swapping between GitHub and Azure DevOps backends. Both platforms are always available simultaneously; the active platform is determined by which agent and MCP server the user invokes.
applyTo: .vscode/mcp.json
---

# Platform Swap Rules

This workspace supports two project management backends — **GitHub** and **Azure DevOps** — via two MCP servers configured simultaneously in `.vscode/mcp.json`. The developer UX (Copilot chat, skill verbs, agent personas) is identical across platforms; only the MCP server and config file differ.

## Platform Mapping

| Concept | GitHub | Azure DevOps |
|---|---|---|
| Work item / Issue | GitHub Issue | ADO Work Item |
| Board / Project | GitHub Projects v2 | ADO Board |
| Code Review / PR | GitHub Pull Request | ADO Pull Request |
| Sprint / Iteration | GitHub Project Iteration | ADO Iteration Path |
| Assignee identifier | GitHub username | ADO display name (email) |
| Priority | Project field (`singleSelectOptionId`) | `Microsoft.VSTS.Common.Priority` (1–4) |
| Config file | `github_devflow/config/github-config.yaml` | `ado_backlog_pipeline/config/ado-config.yaml` |
| MCP server key | `github` | `ado` |
| Planning agent | GitHub Project Manager | ADO Planner |
| Execution agent | GitHub DevOps Engineer | ADO Executor |
| Skills | `github-issues`, `github-projects`, `github-pullrequests` | `ado-workitems` |
| Auth | VS Code GitHub OAuth (automatic) | Browser-based Microsoft login (first use) |

## Swap Rules

- Both MCP servers are always present in `.vscode/mcp.json` — neither is removed to "switch" platforms.
- To work in GitHub mode: invoke the **GitHub Project Manager** or **GitHub DevOps Engineer** agent.
- To work in ADO mode: invoke the **ADO Planner** or **ADO Executor** agent.
- Skills are platform-specific: `github-issues/projects/pullrequests` call the `github` MCP server; `ado-workitems` calls the `ado` MCP server.
- The shared developer vocabulary (create, update, close, assign, sprint, review, merge) maps to equivalent operations per the table above.
- Never direct both MCP servers to write to the same work item simultaneously without explicit cross-platform sync intent.
- When adding a new team member, add them to both `assignee_map` in `github_devflow/config/github-config.yaml` (GitHub username) and in `ado_backlog_pipeline/config/ado-config.yaml` (display name + email).
- When adding a new sprint, add it to both `sprint_map` in github-config.yaml and `iteration_map` in ado-config.yaml.

## MCP Server Configuration Reference

```json
// .vscode/mcp.json — both servers always active
{
  "servers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/"
    },
    "ado": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@azure-devops/mcp", "${input:ado_org}", "-d", "core", "work", "work-items", "repositories", "pipelines"]
    }
  }
}
```
