#!/usr/bin/env python3
"""Log Task tool results returned to the parent agent (postToolUse matcher: Task)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from factory_lib import (
    detect_factory_agent,
    emit,
    is_factory_task_subagent,
    parse_assignment_id,
    parse_tool_input,
    read_stdin_json,
    repo_root,
    run_log_message,
)


def extract_tool_output(data: dict) -> str:
    raw = data.get("tool_output")
    if raw is None:
        return ""
    if isinstance(raw, str):
        return raw.strip()
    return json.dumps(raw, ensure_ascii=False, indent=2)


def main() -> int:
    data = read_stdin_json()
    if (data.get("tool_name") or "") != "Task":
        emit({})
        return 0

    tool_input = parse_tool_input(data)
    prompt = (tool_input.get("prompt") or "").strip()
    description = (tool_input.get("description") or "").strip()
    subagent_type = (tool_input.get("subagent_type") or "").strip()
    output = extract_tool_output(data)

    if not output:
        emit({})
        return 0

    if not is_factory_task_subagent(subagent_type, prompt or description or output):
        emit({})
        return 0

    root = repo_root(data)
    from_agent = detect_factory_agent(prompt, subagent_type) or subagent_type or "subagent"
    assignment_id = (
        parse_assignment_id(output)
        or parse_assignment_id(prompt)
        or parse_assignment_id(description)
        or ""
    )
    summary = f"Task result from `{from_agent}`"
    if assignment_id:
        summary += f" ({assignment_id})"

    run_log_message(
        root,
        agent=from_agent,
        summary=summary,
        from_agent=from_agent,
        to_agent="foreman",
        kind="tool_result",
        body=output,
        assignment_id=assignment_id,
        details={
            k: v
            for k, v in {
                "tool_use_id": data.get("tool_use_id"),
                "conversation_id": data.get("conversation_id"),
                "description": description,
            }.items()
            if v
        },
    )

    emit({})
    return 0


if __name__ == "__main__":
    sys.exit(main())
