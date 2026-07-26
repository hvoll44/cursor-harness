#!/usr/bin/env python3
"""Hooks 1, 2, 4: auto-log, require assignment context, gate auditor."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from factory_lib import (
    assignment_lifecycle_ready,
    assignment_path,
    detect_factory_agent,
    emit,
    has_assignment_context,
    read_assignment_status,
    read_stdin_json,
    repo_root,
    resolve_assignment_id,
    run_log,
    run_log_message,
)


def main() -> int:
    data = read_stdin_json()
    root = repo_root(data)
    task = data.get("task") or ""
    subagent_type = data.get("subagent_type") or ""

    agent = detect_factory_agent(task, subagent_type)
    if not agent:
        emit({"permission": "allow"})
        return 0

    assignment_id = resolve_assignment_id(task)

    # Hook 4: Gate auditor invocation
    if agent == "auditor":
        if not assignment_id:
            emit(
                {
                    "permission": "deny",
                    "user_message": (
                        "Auditor requires an assignment ID "
                        "(e.g. architect-M2-01) in the delegation prompt."
                    ),
                }
            )
            return 0

        path = assignment_path(root, assignment_id)
        status = read_assignment_status(path)
        if status != "completed":
            emit(
                {
                    "permission": "deny",
                    "user_message": (
                        f"Auditor blocked: assignment `{assignment_id}` status is "
                        f"`{status or 'missing'}`, expected `completed`."
                    ),
                }
            )
            return 0

        lifecycle_ready, reason = assignment_lifecycle_ready(root, assignment_id)
        if not lifecycle_ready:
            emit(
                {
                    "permission": "deny",
                    "user_message": (
                        f"Auditor blocked: `{assignment_id}` {reason}. "
                        "Require Foreman delegation plus assignee `started` and "
                        "`completed` entries in factory/log/."
                    ),
                }
            )
            return 0

    # Hook 2: Require assignment context for specialist subagents
    elif agent in {"architect", "implementer", "tester"}:
        if not has_assignment_context(task):
            emit(
                {
                    "permission": "deny",
                    "user_message": (
                        f"Factory `{agent}` subagent requires assignment context: "
                        "include `factory/assignments/<id>.md` or an assignment ID "
                        "(e.g. implementer-M2-01) in the task prompt."
                    ),
                }
            )
            return 0

    # Hook 1: Auto-log subagent start
    summary = f"Subagent `{agent}` started"
    if assignment_id:
        summary += f" for assignment `{assignment_id}`"
    run_log(root, agent, "started", summary, assignment_id=assignment_id or "")

    if task.strip():
        parent = "foreman"
        msg_summary = f"Prompt to `{agent}`"
        if assignment_id:
            msg_summary += f" ({assignment_id})"
        run_log_message(
            root,
            agent=agent,
            summary=msg_summary,
            from_agent=parent,
            to_agent=agent,
            kind="prompt",
            body=task,
            assignment_id=assignment_id or "",
            details={
                k: v
                for k, v in {
                    "subagent_id": data.get("subagent_id"),
                    "subagent_type": subagent_type,
                    "tool_call_id": data.get("tool_call_id"),
                    "parent_conversation_id": data.get("parent_conversation_id"),
                    "conversation_id": data.get("conversation_id"),
                    "subagent_model": data.get("subagent_model"),
                }.items()
                if v
            },
        )

    emit({"permission": "allow"})
    return 0


if __name__ == "__main__":
    sys.exit(main())
