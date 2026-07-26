#!/usr/bin/env python3
"""Hooks 1, 3: auto-log subagent stop; chain auditor after specialist completes."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from factory_lib import (
    detect_factory_agent,
    emit,
    parse_assignment_id,
    read_stdin_json,
    repo_root,
    run_log,
    run_log_message,
)


def main() -> int:
    data = read_stdin_json()
    root = repo_root(data)
    task = data.get("task") or ""
    subagent_type = data.get("subagent_type") or ""
    status = data.get("status") or ""

    agent = detect_factory_agent(task, subagent_type)
    if not agent:
        emit({})
        return 0

    assignment_id = parse_assignment_id(task) or ""
    # A host-level completed status means the subagent run ended, not that its
    # assignment passed its acceptance criteria. The assignee must explicitly
    # log `completed` after updating the assignment, which keeps audit gating
    # tied to an intentional completion claim.
    action = "note"
    summary = f"Subagent `{agent}` {status or 'stopped'}"
    if assignment_id:
        summary += f" for assignment `{assignment_id}`"

    run_log(root, agent, action, summary, assignment_id=assignment_id)

    correlation = {
        k: v
        for k, v in {
            "conversation_id": data.get("conversation_id"),
            "status": status,
            "duration_ms": data.get("duration_ms"),
            "message_count": data.get("message_count"),
            "tool_call_count": data.get("tool_call_count"),
            "agent_transcript_path": data.get("agent_transcript_path"),
            "modified_files": data.get("modified_files"),
        }.items()
        if v is not None and v != "" and v != []
    }

    response_summary = (data.get("summary") or "").strip()
    if response_summary:
        run_log_message(
            root,
            agent=agent,
            summary=f"Response from `{agent}`",
            from_agent=agent,
            to_agent="foreman",
            kind="response",
            body=response_summary,
            assignment_id=assignment_id,
            details=correlation,
        )

    output: dict = {}

    # Hook 3: Chain auditor after architect/implementer/tester completes
    if (
        status == "completed"
        and agent in {"architect", "implementer", "tester"}
        and assignment_id
    ):
        followup = (
            f"Factory hook: `{agent}` finished assignment `{assignment_id}`. "
            "Run the **factory-audit** checklist. If the assignment file status "
            "is `completed`, invoke `/auditor` with:\n\n"
            f"Assignment: factory/assignments/{assignment_id}.md\n\n"
            "Verify all acceptance criteria with evidence."
        )
        output["followup_message"] = followup
        run_log_message(
            root,
            agent="hook",
            summary=f"Follow-up after `{agent}` completed `{assignment_id}`",
            from_agent="hook",
            to_agent="foreman",
            kind="followup",
            body=followup,
            assignment_id=assignment_id,
            details={"trigger_agent": agent, **correlation},
        )

    emit(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
