#!/usr/bin/env python3
"""Log parent→subagent Task tool delegations (preToolUse matcher: Task)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from factory_lib import (
    detect_factory_agent,
    emit,
    infer_parent_agent,
    is_factory_task_subagent,
    parse_assignment_id,
    parse_tool_input,
    read_stdin_json,
    repo_root,
    run_log_message,
)


def main() -> int:
    data = read_stdin_json()
    if (data.get("tool_name") or "") != "Task":
        emit({"permission": "allow"})
        return 0

    tool_input = parse_tool_input(data)
    prompt = (tool_input.get("prompt") or "").strip()
    description = (tool_input.get("description") or "").strip()
    subagent_type = (tool_input.get("subagent_type") or "").strip()

    if not prompt and not description:
        emit({"permission": "allow"})
        return 0

    if not is_factory_task_subagent(subagent_type, prompt or description):
        emit({"permission": "allow"})
        return 0

    root = repo_root(data)
    to_agent = detect_factory_agent(prompt, subagent_type) or subagent_type or "subagent"
    from_agent = infer_parent_agent(data)
    assignment_id = parse_assignment_id(prompt) or parse_assignment_id(description) or ""
    body = prompt or description
    summary = f"Delegated to `{to_agent}`"
    if description:
        summary += f": {description[:120]}"
    elif assignment_id:
        summary += f" ({assignment_id})"

    run_log_message(
        root,
        agent=from_agent,
        summary=summary,
        from_agent=from_agent,
        to_agent=to_agent,
        kind="delegation",
        body=body,
        assignment_id=assignment_id,
        details={
            k: v
            for k, v in {
                "tool_use_id": data.get("tool_use_id"),
                "conversation_id": data.get("conversation_id"),
                "description": description,
                "subagent_type": subagent_type,
            }.items()
            if v
        },
    )

    emit({"permission": "allow"})
    return 0


if __name__ == "__main__":
    sys.exit(main())
