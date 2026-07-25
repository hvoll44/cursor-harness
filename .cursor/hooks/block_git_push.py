#!/usr/bin/env python3
"""Block git push (remote/origin); allow commits and other local git operations."""

from __future__ import annotations

import json
import re
import sys

# Git global options may appear before the subcommand, for example:
# git -C other push, git -c advice.detachedHead=false push, or git.exe push.
GIT_PUSH_RE = re.compile(
    r"\bgit(?:\.exe)?"
    r"(?:\s+(?:-C|-c|--git-dir|--work-tree)(?:=|\s+)\S+)*"
    r"\s+push\b",
    re.IGNORECASE,
)


def is_blocked_push(command: str) -> bool:
    return bool(GIT_PUSH_RE.search(command.strip()))


def main() -> int:
    data = json.loads(sys.stdin.read() or "{}")
    command = data.get("command") or ""

    if is_blocked_push(command):
        print(
            json.dumps(
                {
                    "permission": "deny",
                    "user_message": (
                        "git push is blocked for agents in this project. "
                        "You can commit locally; push to origin manually when ready."
                    ),
                    "agent_message": (
                        f"The command was blocked by the factory git hook: `{command}`\n\n"
                        "Allowed: `git add`, `git commit`, `git status`, `git diff`, "
                        "`git log`, `git branch`, etc.\n"
                        "Not allowed: `git push` (including `git push origin`). "
                        "Tell the user their commits are ready to push when finished."
                    ),
                },
                ensure_ascii=False,
            )
        )
        return 0

    print(json.dumps({"permission": "allow"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
