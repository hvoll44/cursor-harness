#!/usr/bin/env python3
"""Hook 6: Block writes/deletes to paths under done milestones."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from factory_lib import emit, is_protected_path, read_stdin_json, repo_root


def extract_file_path(tool_name: str, tool_input: dict) -> str | None:
    if tool_name in {"Write", "Delete"}:
        return tool_input.get("path") or tool_input.get("file_path")
    if tool_name == "StrReplace":
        return tool_input.get("path")
    return None


def main() -> int:
    data = read_stdin_json()
    root = repo_root(data)
    tool_name = data.get("tool_name") or ""
    tool_input = data.get("tool_input") or {}

    if isinstance(tool_input, str):
        try:
            tool_input = json.loads(tool_input)
        except json.JSONDecodeError:
            tool_input = {}

    file_path = extract_file_path(tool_name, tool_input)
    if not file_path:
        emit({"permission": "allow"})
        return 0

    protected, prefix = is_protected_path(root, file_path)
    if not protected:
        emit({"permission": "allow"})
        return 0

    rel = file_path.replace("\\", "/")
    emit(
        {
            "permission": "deny",
            "user_message": (
                f"Edit blocked: `{rel}` is under done milestone path `{prefix}`. "
                "Ask /system to reopen the milestone in factory/roadmap.md before "
                "editing this path."
            ),
            "agent_message": (
                f"Cannot modify `{rel}` — it belongs to a completed milestone. "
                "Ask /system to reopen the milestone, log the adjustment, and "
                "delegate a rework assignment."
            ),
        }
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
