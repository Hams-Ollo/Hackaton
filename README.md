
# AI Agents Hackathon (Azure + GitHub)

End-to-end agentic automation for SDLC + Ops using **Azure OpenAI**, **Azure Functions**, **Azure AI Search**, and **GitHub Actions**.

## Quick Start
1. Create Azure resources (OpenAI, Functions/Container Apps, AI Search, Key Vault, App Insights).
2. Add GitHub secrets: `AI_PR_REVIEW_FUNC_URL`, `AI_PR_REVIEW_FUNC_KEY`, `AI_CHATOPS_FUNC_URL`, `AI_CHATOPS_FUNC_KEY`.
3. Enable workflows in `.github/workflows/`.
4. Push a PR to see the PR Review Agent in action.

## Repo Layout
See `REPO_STRUCTURE.md` for a full tree.

## Diagrams
All Mermaid diagrams live under `docs/diagrams/` and can be previewed in GitHub.

## Notes
- Uses **Python** agents.
- Integrates via **Actions + GITHUB_TOKEN** (no GitHub App required for MVP).
- Azure Monitor/Log Analytics can be added later for the Log Analyst.
