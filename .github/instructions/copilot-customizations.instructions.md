---
name: Copilot Customization Rules
description: Rules for editing workspace custom agents, skills, and instructions in this repository.
applyTo: .github/**/*.md
---

# Copilot Customization Rules

- Keep repo-wide instructions in `.github/copilot-instructions.md` and avoid duplicating detailed workflow content there.
- Keep skills thin and task-focused. Move long tables and deep reference material into nearby reference files.
- Keep operational code and data outside the skill directory unless the goal is a fully self-contained portable skill package.
- Use custom agents for role-specific operating modes and handoffs, not as a replacement for skills.
- Use instructions for durable conventions and scoped editing rules, not step-by-step task execution.
- When documenting MCP, separate live tool access from deterministic script workflows.
