#!/usr/bin/env python3
"""Hook 5: Inject project vision and roadmap context at session start."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from factory_lib import (
    emit,
    has_substantive_factory_context,
    read_roadmap_summary,
    read_stdin_json,
    repo_root,
)


def main() -> int:
    data = read_stdin_json()
    root = repo_root(data)
    if not has_substantive_factory_context(root):
        emit({})
        return 0

    context = read_roadmap_summary(root)

    if len(context) < 80:
        emit({})
        return 0

    emit({"additional_context": context})
    return 0


if __name__ == "__main__":
    sys.exit(main())
