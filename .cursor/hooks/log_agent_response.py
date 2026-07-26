#!/usr/bin/env python3
"""Log assistant responses that mention factory assignments or agents."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from factory_lib import (
    detect_factory_agent,
    emit,
    parse_assignment_id,
    read_stdin_json,
    repo_root,
    run_log_message,
)

FACTORY_MENTION = re.compile(
    r"\b(foreman|architect|implementer|tester|auditor)\b|"
    r"factory/assignments/|"
    r"/(?:architect|implementer|tester|auditor|foreman)\b",
    re.I,
)


def main() -> int:
    data = read_stdin_json()
    text = (data.get("text") or "").strip()
    if not text or not FACTORY_MENTION.search(text):
        emit({})
        return 0

    root = repo_root(data)
    assignment_id = parse_assignment_id(text) or ""
    agent = detect_factory_agent(text) or "foreman"

    run_log_message(
        root,
        agent=agent,
        summary="Assistant response (factory-related)",
        from_agent=agent,
        to_agent="user",
        kind="assistant",
        body=text,
        assignment_id=assignment_id,
        details={
            k: v
            for k, v in {
                "conversation_id": data.get("conversation_id"),
                "generation_id": data.get("generation_id"),
            }.items()
            if v
        },
    )

    emit({})
    return 0


if __name__ == "__main__":
    sys.exit(main())
