#!/usr/bin/env python3
"""Hook 7: Warn when edits fall outside architecture folder structure."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from factory_lib import emit, is_in_scope, read_stdin_json, repo_root


def extract_write_path(tool_input: dict) -> str | None:
    return tool_input.get("path") or tool_input.get("file_path")


def main() -> int:
    data = read_stdin_json()
    root = repo_root(data)
    tool_input = data.get("tool_input") or {}

    if isinstance(tool_input, str):
        try:
            tool_input = json.loads(tool_input)
        except json.JSONDecodeError:
            tool_input = {}

    file_path = extract_write_path(tool_input)
    if not file_path:
        emit({})
        return 0

    in_scope, rel = is_in_scope(root, file_path)
    if in_scope:
        emit({})
        return 0

    emit(
        {
            "additional_context": (
                f"Factory scope warning: `{rel}` is outside paths declared in "
                "`docs/architecture.md` Folder Structure section. "
                "Confirm with /architect or update the architecture doc."
            )
        }
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
