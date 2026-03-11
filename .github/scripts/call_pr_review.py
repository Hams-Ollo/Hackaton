
#!/usr/bin/env python3
"""Call PR Review Agent, annotate PR, post comment, and set pass/fail gate."""
import os
import json
import argparse
import requests

MAX_ANNOTATIONS = 50  # GitHub UI caps

SEVERITY_TO_LEVEL = {
    "error": "error",
    "warn": "warning",
    "warning": "warning",
    "info": "notice",
}

BLOCKING_SEVERITIES = {"error"}  # policy-aligned


def get_changed_files(repo: str, pr_number: int, github_token: str):
    owner, name = repo.split('/')
    url = f"https://api.github.com/repos/{owner}/{name}/pulls/{pr_number}/files"
    headers = {"Authorization": f"Bearer {github_token}", "Accept": "application/vnd.github+json"}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    files = r.json()
    return [{"filename": f["filename"], "patch": f.get("patch", "")} for f in files]


def post_pr_comment(repo: str, pr_number: int, github_token: str, body: str):
    owner, name = repo.split('/')
    url = f"https://api.github.com/repos/{owner}/{name}/issues/{pr_number}/comments"
    headers = {"Authorization": f"Bearer {github_token}", "Accept": "application/vnd.github+json"}
    r = requests.post(url, headers=headers, json={"body": body}, timeout=30)
    r.raise_for_status()
    return r.json()


def print_annotation(item):
    path = item.get('file') or 'UNKNOWN_FILE'
    level = SEVERITY_TO_LEVEL.get(str(item.get('severity', 'info')).lower(), 'notice')
    line = int(item.get('line') or 1)
    # GitHub workflow command for annotations
    msg = item.get('message', 'No message provided').replace('
', ' ')
    print(f"::{level} file={path},line={line}::{msg}")


def write_step_summary(result):
    summary_path = os.getenv('GITHUB_STEP_SUMMARY')
    if not summary_path:
        return
    items_md = []
    for it in result.get('items', []):
        loc = f" (line {it.get('line')})" if it.get('line') else ''
        patch = f"
```diff
{it.get('suggestion_patch')}
```" if it.get('suggestion_patch') else ''
        items_md.append(f"- **{str(it.get('severity','info')).upper()}** — `{it.get('file','')}`{loc}: {it.get('message','')}{patch}")
    items_md_str = "
".join(items_md) or "(no specific items reported)"
    with open(summary_path, 'a', encoding='utf-8') as f:
        f.write(f"""
### AI PR Review (verdict: **{result.get('verdict','unknown')}**)
{result.get('summary','(no summary)')}

**Findings:**
{items_md_str}
""")


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--repo', required=True)
    p.add_argument('--pr', type=int, required=True)
    p.add_argument('--func-url', required=True)
    p.add_argument('--func-key', required=True)
    p.add_argument('--github-token', required=True)
    p.add_argument('--head-sha', required=False)  # optional if you later use Statuses API
    args = p.parse_args()

    files = get_changed_files(args.repo, args.pr, args.github_token)

    payload = {
        "repo": args.repo,
        "prNumber": args.pr,
        "files": files,
    }
    headers = {"x-functions-key": args.func_key, "Content-Type": "application/json"}
    resp = requests.post(args.func_url.rstrip('/') + '/pr-review', headers=headers, data=json.dumps(payload), timeout=120)
    resp.raise_for_status()
    result = resp.json()

    # Post a consolidated PR comment (human-friendly)
    items_md = []
    for it in result.get('items', []):
        loc = f" (line {it.get('line')})" if it.get('line') else ''
        patch = f"
```diff
{it.get('suggestion_patch')}
```" if it.get('suggestion_patch') else ''
        items_md.append(f"- **{str(it.get('severity','info')).upper()}** — `{it.get('file','')}`{loc}: {it.get('message','')}{patch}")
    items_md_str = "
".join(items_md) or "(no specific items reported)"
    body = f"""
### AI PR Review (verdict: **{result.get('verdict','unknown')}**)
{result.get('summary','(no summary)')}

**Findings:**
{items_md_str}

_This is a preview. Human reviewers should still validate business logic and architecture._
"""
    post_pr_comment(args.repo, args.pr, args.github_token, body)

    # Emit GitHub Action annotations for line-level visibility (no GitHub App required)
    for i, it in enumerate(result.get('items', [])[:MAX_ANNOTATIONS]):
        print_annotation(it)

    # Write to step summary
    write_step_summary(result)

    # Gate: fail step if blocking severity present
    blocking_found = any(str(it.get('severity','')).lower() in BLOCKING_SEVERITIES for it in result.get('items', []))
    if blocking_found or result.get('verdict') in ('block', 'changes_requested'):
        # Non-zero exit -> job failure -> branch protection blocks merge
        print("::group::AI gate result")
        print("Blocking findings present. Failing the job to enforce policy.")
        print("::endgroup::")
        raise SystemExit(1)

    print("All good: no blocking findings.")

if __name__ == '__main__':
    main()
