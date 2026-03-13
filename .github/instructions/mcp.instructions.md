---
name: MCP Configuration Rules
description: Rules for workspace MCP configuration and related documentation.
applyTo: .vscode/mcp.json
---

# MCP Configuration Rules

- Store shared workspace MCP server configuration in `.vscode/mcp.json`.
- Do not hardcode secrets. Use supported variables, env files, or other secret indirection.
- Reserve MCP for live service tools, prompts, and resources that are better than script orchestration.
- Keep deterministic batch workflows in scripts rather than pushing them into MCP unless there is a clear runtime benefit.
- Document required trust, auth, and startup assumptions for every server added.
