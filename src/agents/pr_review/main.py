
"PR Review Agent (HTTP) - Placeholder implementation."

# Exposes POST /pr-review
# Accepts: repo, prNumber, githubToken (optional), files[] (filename, patch)
# Calls Azure OpenAI (placeholder) to get structured JSON review
# Returns JSON: {summary, items:[{file,line?,severity,message,suggestion_patch?}], verdict}

import os
import json
from typing import List, Dict, Any
from flask import Flask, request, jsonify

# Optional: import requests for GitHub API use if you want to fetch diffs server-side
import requests

app = Flask(__name__)

# --- Settings ---
AOAI_ENDPOINT = os.getenv("AOAI_ENDPOINT", "https://<your-endpoint>.openai.azure.com/")
AOAI_DEPLOYMENT = os.getenv("AOAI_DEPLOYMENT", "gpt-4o-mini")
AOAI_API_KEY = os.getenv("AOAI_API_KEY", "<set-in-keyvault-or-env>")

def fetch_changed_files(repo: str, pr_number: int, github_token: str) -> List[Dict[str, Any]]:
    """Fetch changed files/patches from GitHub (server-side)."""
    owner, name = repo.split("/")
    url = f"https://api.github.com/repos/{owner}/{name}/pulls/{pr_number}/files"
    headers = {"Authorization": f"Bearer {github_token}", "Accept": "application/vnd.github+json"}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    files = r.json()
    return [{"filename": f["filename"], "patch": f.get("patch", "")} for f in files]

def build_prompt(files: List[Dict[str, Any]], standards_snippets: str = "") -> str:
    diffs = []
    for f in files:
        patch = (f.get("patch") or "")[:8000]
        diffs.append(f"FILE: {f['filename']}
PATCH:
{patch}")
    diff_text = "

".join(diffs)
    prompt = f"""
You are a senior code reviewer. Review ONLY the changed hunks below.
Prioritize correctness, security, performance, and maintainability.
Use the organization standards if relevant. Be concise and specific.
Return JSON: {{summary, items:[{{file, line?, severity, message, suggestion_patch?}}], verdict}}

STANDARDS (optional):
{standards_snippets}

DIFF:
{diff_text}
"""
    return prompt


def call_aoai(prompt: str) -> Dict[str, Any]:
    """Placeholder call to Azure OpenAI. Replace with official SDK call."""
    # Example shape to guide downstream scripts
    # TODO: Implement with azure.ai.openai SDK and response_format JSON
    return {
        "summary": "Placeholder summary - replace with real AOAI call.",
        "items": [
            {
                "file": "example.py",
                "severity": "warn",
                "message": "Consider checking for None before calling len().",
                "suggestion_patch": "- if len(x) > 0:
+ if x is not None and len(x) > 0:"
            }
        ],
        "verdict": "changes_requested"
    }


@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}, 200


@app.route("/pr-review", methods=["POST"])
def pr_review():
    payload = request.get_json(force=True)
    repo = payload.get("repo")
    pr_number = int(payload.get("prNumber"))
    github_token = payload.get("githubToken")
    files = payload.get("files")

    # If files not provided, fetch from GitHub (requires token)
    if not files:
        if not github_token:
            return jsonify({"error": "githubToken required if files are not provided"}), 400
        files = fetch_changed_files(repo, pr_number, github_token)

    # TODO: Optionally retrieve RAG snippets from Azure AI Search
    standards_snippets = ""  # placeholder

    prompt = build_prompt(files, standards_snippets)
    review = call_aoai(prompt)
    return jsonify(review), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
