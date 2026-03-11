
# Pull Request (PR) Review Policy

**Objective:** Accelerate code reviews while improving quality, security, and maintainability using an AI PR Review Agent + human approver-in-the-loop.

---
## 1. Scope
Applies to all application code, infrastructure-as-code, and scripts in this repository. The AI Agent provides a first-pass review; humans focus on business logic and architectural concerns.

---
## 2. PR Size & Expectations
- **XS (≤50 LOC changed):** May auto-approve if AI verdict = `approve` and CI = green.
- **S (51–200 LOC):** Human skim review after AI passes.
- **M (201–400 LOC):** Human review required; address AI findings first.
- **L/XL (>400 LOC):** Must be split unless justified; AI will flag `needs-split`.

**PR hygiene (required):**
- Clear title and description (what/why). Link issues.
- Include screenshots for UI changes.
- Call out risky areas or migrations.

---
## 3. Quality Gates (merge blocked if any fail)
- **Security:** Any `error` severity in security -> block until fixed.
- **Correctness:** `error` severity correctness issues -> block.
- **Tests:** Modified functions lack tests -> block unless tagged `test-exempt` with rationale.
- **CI:** All checks green (build, unit tests, lint). 

Advisory (non-blocking): style, naming, comments, minor perf.

---
## 4. Severity & Labels
- `error` -> must fix before merge
- `warn` -> should fix or justify
- `info` -> optional, educational

AI adds labels: `ai-reviewed`, `needs-tests`, `security`, `performance`, `needs-split`.

---
## 5. Security Rules (minimum)
- No secrets in code/logs. Use Key Vault / env vars.
- Validate and sanitize inputs. Avoid shelling out.
- Parameterized queries only; prevent injection.
- Avoid unsafe deserialization; prefer safe parsers.

---
## 6. Testing Rules
- Add/Update tests for changed logic.
- Ensure happy-path + at least one edge case.
- Keep tests deterministic and fast (<1s each when possible).

---
## 7. Standards & RAG
The agent retrieves coding standards and examples via Azure AI Search. If the agent cites a standard, link appears in the PR comment; if no relevant standard exists, prefer consistency with existing codebase.

---
## 8. Review SLA
- AI review: < 60 seconds.
- Human review windows: 2 per day (late morning / late afternoon). Avoid ad-hoc requests.

---
## 9. ChatOps Commands
- `/ai review` – re-run the review on demand.
- `/ai tests` – suggest missing tests for changed files.
- `/ai summarize` – summarize changes & risk.

---
## 10. Governance & Safety
- Agent runs with least privilege; no write to repo without review.
- PII & secrets filtered by prompts; logs exclude sensitive data.

---
## 11. Observability & Metrics
- PR latency, AI suggestion acceptance rate, false-positive rate, coverage delta on touched files.

---
## 12. Exceptions
- Maintainers can override gates with `/override <reason>`; all overrides are reported in weekly digest.
