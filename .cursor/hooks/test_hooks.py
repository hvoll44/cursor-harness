#!/usr/bin/env python3
"""Smoke tests for factory hooks (run from repo root)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / ".cursor" / "hooks"


def run_hook(script: str, payload: dict) -> dict:
    result = subprocess.run(
        [sys.executable, str(HOOKS / script)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=ROOT,
    )
    out = result.stdout.strip()
    return json.loads(out) if out else {}


def test_session_start():
    out = run_hook("session_start.py", {"workspace_roots": [str(ROOT)]})
    assert "additional_context" in out
    assert "Software Development Factory" in out["additional_context"]
    print("session_start: ok")


def test_subagent_start_denies_missing_assignment():
    out = run_hook(
        "subagent_start.py",
        {
            "workspace_roots": [str(ROOT)],
            "task": "Design the API layer as architect",
            "subagent_type": "architect",
        },
    )
    assert out.get("permission") == "deny"
    print("subagent_start deny: ok")


def test_subagent_start_allows_with_assignment():
    out = run_hook(
        "subagent_start.py",
        {
            "workspace_roots": [str(ROOT)],
            "task": "Assignment factory/assignments/architect-M1-01.md — design layout",
            "subagent_type": "architect",
        },
    )
    assert out.get("permission") == "allow"
    print("subagent_start allow: ok")


def test_subagent_stop_followup():
    out = run_hook(
        "subagent_stop.py",
        {
            "workspace_roots": [str(ROOT)],
            "task": "architect-M2-01 done",
            "subagent_type": "architect",
            "status": "completed",
        },
    )
    assert "followup_message" in out
    assert "/auditor" in out["followup_message"]
    print("subagent_stop followup: ok")


def test_protect_done_milestones_allows_unprotected():
    out = run_hook(
        "protect_done_milestones.py",
        {
            "workspace_roots": [str(ROOT)],
            "tool_name": "Write",
            "tool_input": {"path": str(ROOT / "e2e" / "new.spec.ts")},
        },
    )
    assert out.get("permission") == "allow"
    print("protect_done allow: ok")


def test_block_git_push_denies():
    out = run_hook(
        "block_git_push.py",
        {"command": "git push -u origin main"},
    )
    assert out.get("permission") == "deny"
    print("block_git_push deny: ok")


def test_block_git_push_allows_commit():
    out = run_hook(
        "block_git_push.py",
        {"command": "git commit -m \"feat: add factory hooks\""},
    )
    assert out.get("permission") == "allow"
    print("block_git_push allow commit: ok")


def test_subagent_stop_followup_implementer():
    out = run_hook(
        "subagent_stop.py",
        {
            "workspace_roots": [str(ROOT)],
            "task": "implementer-M2-01 complete",
            "subagent_type": "implementer",
            "status": "completed",
            "summary": "Built playable Tetris with SRS rotation and HUD.",
        },
    )
    assert "followup_message" in out
    assert "/auditor" in out["followup_message"]
    print("subagent_stop implementer followup: ok")


def test_log_task_delegation():
    out = run_hook(
        "log_task_delegation.py",
        {
            "workspace_roots": [str(ROOT)],
            "tool_name": "Task",
            "tool_input": {
                "prompt": "Assignment factory/assignments/tester-M3-01.md — write e2e tests",
                "description": "E2E coverage",
                "subagent_type": "tester",
            },
            "tool_use_id": "tool-123",
        },
    )
    assert out.get("permission") == "allow"
    print("log_task_delegation: ok")


def test_log_task_result():
    out = run_hook(
        "log_task_result.py",
        {
            "workspace_roots": [str(ROOT)],
            "tool_name": "Task",
            "tool_input": {
                "prompt": "tester-M3-01",
                "subagent_type": "tester",
            },
            "tool_output": "E2E tests added and passing.",
        },
    )
    assert out == {}
    print("log_task_result: ok")


def test_log_agent_response_skips_non_factory():
    out = run_hook(
        "log_agent_response.py",
        {"workspace_roots": [str(ROOT)], "text": "Here is a generic answer."},
    )
    assert out == {}
    print("log_agent_response skip: ok")


def test_log_agent_response_logs_factory():
    out = run_hook(
        "log_agent_response.py",
        {
            "workspace_roots": [str(ROOT)],
            "text": "Delegated implementer-M2-01 to /implementer for core game work.",
        },
    )
    assert out == {}
    print("log_agent_response factory: ok")


def test_view_messages_script():
    result = subprocess.run(
        [sys.executable, str(ROOT / ".cursor/skills/factory-log/scripts/view-messages.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Factory conversation log" in result.stdout
    print("view_messages: ok")


def main() -> int:
    tests = [
        test_session_start,
        test_subagent_start_denies_missing_assignment,
        test_subagent_start_allows_with_assignment,
        test_subagent_stop_followup,
        test_subagent_stop_followup_implementer,
        test_log_task_delegation,
        test_log_task_result,
        test_log_agent_response_skips_non_factory,
        test_log_agent_response_logs_factory,
        test_view_messages_script,
        test_protect_done_milestones_allows_unprotected,
        test_block_git_push_denies,
        test_block_git_push_allows_commit,
    ]
    for test in tests:
        test()
    print(f"\n{len(tests)} hook tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
