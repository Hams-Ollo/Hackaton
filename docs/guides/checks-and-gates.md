
# Checks & Gates (without a GitHub App)

This workflow uses **GitHub Action annotations** and **job failure** to create a merge gate without requiring a GitHub App. It:

- Prints annotations via workflow commands (visible in PR Checks UI and file diff).
- Fails the job when blocking severities are present.
- You can enforce this gate by configuring **Branch protection rules** to require the workflow to pass before merge.

> Note: GitHub's **Checks API** (creating custom check runs with annotations) is designed for **GitHub Apps**. Since this MVP uses GITHUB_TOKEN (no App), we rely on Action annotations + job status instead.

## Branch Protection
1. Go to **Settings > Branches > Branch protection rules**.
2. Add a rule for your default branch.
3. Enable **Require status checks to pass before merging**.
4. Select the workflow: **ai-pr-review-and-tests**.

## Policy Thresholds
- Blocking severities: `error` (security/correctness).
- Non-blocking: `warn`, `info`.

You can adjust thresholds in `.github/scripts/call_pr_review.py`.
