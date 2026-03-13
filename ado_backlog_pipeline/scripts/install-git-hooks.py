#!/usr/bin/env python3
"""
install-git-hooks.py  (ado_backlog_pipeline bundle)
======================================================
Install or uninstall the post-push git hook that automatically runs
commit-ado-sync.py after every git push.

On Windows, Git hooks require Git Bash or Git for Windows.
A PowerShell profile alias alternative is also printed for teams
who prefer the PowerShell workflow.

Usage
-----
  python install-git-hooks.py           # install the post-push hook
  python install-git-hooks.py --remove  # uninstall the hook
  python install-git-hooks.py --status  # show current hook status
"""

import sys
import argparse
import textwrap
from pathlib import Path

SCRIPT_DIR    = Path(__file__).resolve().parent
BUNDLE_DIR    = SCRIPT_DIR.parent
WORKSPACE_DIR = BUNDLE_DIR.parent

HOOKS_DIR     = WORKSPACE_DIR / ".git" / "hooks"
HOOK_FILE     = HOOKS_DIR / "post-push"
SYNC_SCRIPT   = BUNDLE_DIR / "scripts" / "commit-ado-sync.py"

# Use forward slashes for Git Bash compatibility on Windows
SYNC_SCRIPT_POSIX = SYNC_SCRIPT.as_posix()


HOOK_CONTENT = f"""\
#!/usr/bin/env bash
# ADO Backlog Automation — post-push hook
# Auto-syncs commits referencing AB#ID to Azure DevOps after each push.
# To disable: python ado_backlog_pipeline/scripts/install-git-hooks.py --remove

set -e

SCRIPT="{SYNC_SCRIPT_POSIX}"

if [ -f "$SCRIPT" ]; then
    echo ""
    echo "[ADO Sync] Running commit-ado-sync.py --since-push ..."
    python "$SCRIPT" --since-push
else
    echo "[ADO Sync] WARNING: sync script not found at $SCRIPT"
fi
"""

POWERSHELL_ALIAS_HINT = f"""\
# ─────────────────────────────────────────────────────────────────────────
# PowerShell Profile Aliases (alternative to git hook on Windows)
# Add these lines to your PowerShell profile ($PROFILE) for quick access.
# ─────────────────────────────────────────────────────────────────────────
function ado-sync     {{ python "{SYNC_SCRIPT_POSIX}" --since-push }}
function ado-sync-dry {{ python "{SYNC_SCRIPT_POSIX}" --since-push --dry-run }}
function ado-pull     {{ python "{(BUNDLE_DIR / "scripts" / "pull-ado-workitems.py").as_posix()}" }}
function ado-pull-dry {{ python "{(BUNDLE_DIR / "scripts" / "pull-ado-workitems.py").as_posix()}" --dry-run }}
function ado-report   {{ python "{(BUNDLE_DIR / "scripts" / "generate-ado-report.py").as_posix()}" --all-active }}
# ─────────────────────────────────────────────────────────────────────────
"""


def install() -> None:
    if not HOOKS_DIR.exists():
        print(f"[ERROR] .git/hooks directory not found at: {HOOKS_DIR}")
        print("        Are you running this from inside a git repository?")
        sys.exit(1)

    if HOOK_FILE.exists():
        print(f"[INFO]  post-push hook already exists at: {HOOK_FILE}")
        answer = input("        Overwrite? [y/N] ").strip().lower()
        if answer != "y":
            print("        Cancelled."); return

    HOOK_FILE.write_text(HOOK_CONTENT, encoding="utf-8")

    # Make executable on Unix/Mac (no-op on Windows but harmless)
    try:
        import stat
        current = HOOK_FILE.stat().st_mode
        HOOK_FILE.chmod(current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except Exception:
        pass

    print(f"[OK]    post-push hook installed -> {HOOK_FILE}")
    print()
    print("        After every 'git push', commit-ado-sync.py will run automatically.")
    print()
    print("        ⚠  Windows note: git hooks require Git Bash or Git for Windows.")
    print("           If you use PowerShell as your main terminal, use the aliases below instead:")
    print()
    print(textwrap.indent(POWERSHELL_ALIAS_HINT, "        "))


def remove() -> None:
    if not HOOK_FILE.exists():
        print(f"[INFO]  No post-push hook found at: {HOOK_FILE}"); return
    HOOK_FILE.unlink()
    print(f"[OK]    post-push hook removed from: {HOOK_FILE}")


def status() -> None:
    print(f"  Hook file  : {HOOK_FILE}")
    print(f"  Installed  : {'YES ✓' if HOOK_FILE.exists() else 'NO'}")
    print(f"  Sync script: {SYNC_SCRIPT}")
    print(f"  Script exists: {'YES ✓' if SYNC_SCRIPT.exists() else 'NO ✗'}")
    print()
    print("  PowerShell alias commands (run once, add to $PROFILE):")
    print()
    print(textwrap.indent(POWERSHELL_ALIAS_HINT, "  "))


def main():
    parser = argparse.ArgumentParser(
        description="Install/remove ADO post-push git hook"
    )
    parser.add_argument("--remove", action="store_true", help="Remove the hook")
    parser.add_argument("--status", action="store_true", help="Show hook status")
    args = parser.parse_args()

    if args.status:
        status()
    elif args.remove:
        remove()
    else:
        install()


if __name__ == "__main__":
    main()
