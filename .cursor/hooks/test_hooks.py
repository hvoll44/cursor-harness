#!/usr/bin/env python3
"""Smoke tests for factory hooks (run from repo root)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / ".cursor" / "hooks"
WORKSPACE_ROOT = ROOT
sys.path.insert(0, str(HOOKS))

import factory_lib
import sync_gitignore


def run_hook(script: str, payload: dict) -> dict:
    payload = {**payload, "workspace_roots": [str(WORKSPACE_ROOT)]}
    result = subprocess.run(
        [sys.executable, str(HOOKS / script)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=ROOT,
    )
    out = result.stdout.strip()
    return json.loads(out) if out else {}


def write_assignment(assignment_id: str, agent: str, status: str = "completed"):
    path = WORKSPACE_ROOT / "factory" / "assignments" / f"{assignment_id}.md"
    path.write_text(
        "| Field | Value |\n"
        "|-------|-------|\n"
        f"| **Agent** | `{agent}` |\n"
        f"| **Status** | `{status}` |\n",
        encoding="utf-8",
    )


def write_log_entries(*entries: dict):
    log = WORKSPACE_ROOT / "factory" / "log" / "events.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(
        "\n".join(json.dumps(entry) for entry in entries) + "\n",
        encoding="utf-8",
    )


def write_done_milestone(status: str = "done"):
    (WORKSPACE_ROOT / "factory" / "roadmap.md").write_text(
        "## Milestones\n\n"
        "| ID | Milestone | Owner | Status |\n"
        "|----|-----------|-------|--------|\n"
        f"| M1 | Test | implementer | {status} |\n",
        encoding="utf-8",
    )
    (WORKSPACE_ROOT / "factory" / "milestone-paths.json").write_text(
        json.dumps({"M1": ["src/"]}),
        encoding="utf-8",
    )


def test_session_start():
    out = run_hook("session_start.py", {})
    assert "additional_context" in out
    assert "Software Development Factory" in out["additional_context"]
    print("session_start: ok")


def test_session_start_skips_placeholder_templates():
    (WORKSPACE_ROOT / "factory" / "project-vision.md").write_text(
        "## Summary\n\n## Success Criteria\n\n", encoding="utf-8"
    )
    (WORKSPACE_ROOT / "factory" / "roadmap.md").write_text(
        "## Milestones\n\n"
        "| ID | Milestone | Owner | Status |\n"
        "|----|-----------|-------|--------|\n"
        "| _none_ | — | — | — |\n",
        encoding="utf-8",
    )
    out = run_hook("session_start.py", {})
    assert out == {}
    print("session_start placeholder: ok")


def test_subagent_start_denies_missing_assignment():
    out = run_hook(
        "subagent_start.py",
        {
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
            "task": "Assignment factory/assignments/architect-M1-01.md — design layout",
            "subagent_type": "architect",
        },
    )
    assert out.get("permission") == "allow"
    print("subagent_start allow: ok")


def test_auditor_denies_wrong_agent_logs():
    assignment_id = "implementer-M1-01"
    write_assignment(assignment_id, "implementer")
    write_log_entries(
        {"agent": "foreman", "action": "delegated", "assignment_id": assignment_id},
        {"agent": "foreman", "action": "started", "assignment_id": assignment_id},
        {"agent": "foreman", "action": "completed", "assignment_id": assignment_id},
    )
    out = run_hook(
        "subagent_start.py",
        {"task": f"Audit {assignment_id}", "subagent_type": "auditor"},
    )
    assert out.get("permission") == "deny"
    assert "assignee" in out.get("user_message", "")
    print("auditor denies wrong agent logs: ok")


def test_auditor_allows_assignee_lifecycle():
    assignment_id = "implementer-M1-02"
    write_assignment(assignment_id, "implementer")
    write_log_entries(
        {"agent": "foreman", "action": "delegated", "assignment_id": assignment_id},
        {"agent": "implementer", "action": "started", "assignment_id": assignment_id},
        {"agent": "implementer", "action": "completed", "assignment_id": assignment_id},
    )
    out = run_hook(
        "subagent_start.py",
        {
            "task": f"Assignment: factory/assignments/{assignment_id}.md",
            "subagent_type": "auditor",
        },
    )
    assert out.get("permission") == "allow"
    print("auditor allows assignee lifecycle: ok")


def test_auditor_accepts_legacy_system_delegation():
    assignment_id = "implementer-M1-03"
    write_assignment(assignment_id, "implementer")
    write_log_entries(
        {"agent": "system", "action": "delegated", "assignment_id": assignment_id},
        {"agent": "implementer", "action": "started", "assignment_id": assignment_id},
        {"agent": "implementer", "action": "completed", "assignment_id": assignment_id},
    )
    out = run_hook(
        "subagent_start.py",
        {
            "task": f"Assignment: factory/assignments/{assignment_id}.md",
            "subagent_type": "auditor",
        },
    )
    assert out.get("permission") == "allow"
    print("auditor accepts legacy System delegation: ok")


def test_subagent_stop_followup():
    out = run_hook(
        "subagent_stop.py",
        {
            "task": "architect-M2-01 done",
            "subagent_type": "architect",
            "status": "completed",
        },
    )
    assert "followup_message" in out
    assert "/auditor" in out["followup_message"]
    entries = [
        json.loads(line)
        for path in (WORKSPACE_ROOT / "factory" / "log").glob("*.jsonl")
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert not any(
        entry.get("assignment_id") == "architect-M2-01"
        and entry.get("action") == "completed"
        for entry in entries
    )
    print("subagent_stop followup: ok")


def test_protect_done_milestones_allows_unprotected():
    out = run_hook(
        "protect_done_milestones.py",
        {
            "tool_name": "Write",
            "tool_input": {"path": str(WORKSPACE_ROOT / "e2e" / "new.spec.ts")},
        },
    )
    assert out.get("permission") == "allow"
    print("protect_done allow: ok")


def test_protect_done_milestones_denies_hotfix_phrase():
    write_done_milestone()
    out = run_hook(
        "protect_done_milestones.py",
        {
            "tool_name": "Write",
            "tool_input": {"path": str(WORKSPACE_ROOT / "src" / "protected.py")},
            "agent_message": "Apply a hotfix to this completed work.",
        },
    )
    assert out.get("permission") == "deny"
    print("protect_done denies hotfix phrase: ok")


def test_protect_done_milestones_allows_reopened_milestone():
    write_done_milestone("in_progress")
    out = run_hook(
        "protect_done_milestones.py",
        {
            "tool_name": "Write",
            "tool_input": {"path": str(WORKSPACE_ROOT / "src" / "reworked.py")},
        },
    )
    assert out.get("permission") == "allow"
    print("protect_done allows reopened milestone: ok")


def test_scope_parser_uses_structure_section_only():
    architecture = WORKSPACE_ROOT / "docs" / "architecture.md"
    architecture.parent.mkdir(parents=True, exist_ok=True)
    architecture.write_text(
        "# Architecture\n\n"
        "Unrelated reference: `orphan/pkg`.\n\n"
        "## Folder Structure\n\n"
        "```text\n"
        "└── src/app/\n"
        "```\n\n"
        "## Interfaces\n\n"
        "Also unrelated: `other/pkg`.\n",
        encoding="utf-8",
    )
    assert factory_lib.parse_architecture_paths(WORKSPACE_ROOT) == ["src/app"]
    out = run_hook(
        "warn_out_of_scope.py",
        {
            "tool_name": "Write",
            "tool_input": {"path": str(WORKSPACE_ROOT / "orphan" / "pkg" / "x.py")},
        },
    )
    assert "additional_context" in out
    print("scope parser section only: ok")


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


def test_block_git_push_denies_global_option():
    out = run_hook(
        "block_git_push.py",
        {"command": "git -C ../other push origin main"},
    )
    assert out.get("permission") == "deny"
    print("block_git_push global option: ok")


def test_run_log_reports_failure():
    previous_script = factory_lib.LOG_SCRIPT
    failing_script = WORKSPACE_ROOT / "failing_log.py"
    failing_script.write_text("import sys; sys.exit(1)\n", encoding="utf-8")
    factory_lib.LOG_SCRIPT = failing_script
    stderr = StringIO()
    try:
        with redirect_stderr(stderr):
            assert not factory_lib.run_log(
                WORKSPACE_ROOT, "foreman", "note", "Expected failing log"
            )
    finally:
        factory_lib.LOG_SCRIPT = previous_script
    assert "factory-log failed" in stderr.getvalue()
    print("run_log failure reporting: ok")


def test_gitignore_sync_adds_detected_artifact_once():
    cache = WORKSPACE_ROOT / ".pytest_cache"
    cache.mkdir()
    (cache / "state.json").write_text("{}", encoding="utf-8")

    assert ".pytest_cache/" in sync_gitignore.sync_gitignore(WORKSPACE_ROOT)
    assert sync_gitignore.sync_gitignore(WORKSPACE_ROOT) == []
    gitignore = (WORKSPACE_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert gitignore.count(".pytest_cache/") == 1
    print("gitignore sync adds detected artifact once: ok")


def test_gitignore_sync_never_ignores_tracked_artifact():
    cache = WORKSPACE_ROOT / ".mypy_cache"
    cache.mkdir()
    state = cache / "state.json"
    state.write_text("{}", encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(WORKSPACE_ROOT), "add", str(state.relative_to(WORKSPACE_ROOT))],
        check=True,
        capture_output=True,
        text=True,
    )

    assert ".mypy_cache/" not in sync_gitignore.sync_gitignore(WORKSPACE_ROOT)
    gitignore = (WORKSPACE_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".mypy_cache/" not in gitignore
    print("gitignore sync skips tracked artifact: ok")


def test_subagent_stop_followup_implementer():
    out = run_hook(
        "subagent_stop.py",
        {
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
        {"text": "Here is a generic answer."},
    )
    assert out == {}
    print("log_agent_response skip: ok")


def test_log_agent_response_logs_factory():
    out = run_hook(
        "log_agent_response.py",
        {
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
        env={**os.environ, "FACTORY_ROOT": str(WORKSPACE_ROOT)},
    )
    assert result.returncode == 0
    assert "Factory conversation log" in result.stdout
    print("view_messages: ok")


def main() -> int:
    global WORKSPACE_ROOT
    with tempfile.TemporaryDirectory() as directory:
        WORKSPACE_ROOT = Path(directory)
        subprocess.run(
            ["git", "init", "-q", str(WORKSPACE_ROOT)],
            check=True,
            capture_output=True,
            text=True,
        )
        factory = WORKSPACE_ROOT / "factory"
        (factory / "assignments").mkdir(parents=True)
        (factory / "project-vision.md").write_text(
            "## Summary\n\nTest factory vision.\n", encoding="utf-8"
        )
        (factory / "roadmap.md").write_text(
            "## Current Phase\n\nTest phase.\n\n"
            "## Milestones\n\n"
            "| ID | Milestone | Owner | Status |\n"
            "|----|-----------|-------|--------|\n"
            "| M1 | Test | architect | pending |\n",
            encoding="utf-8",
        )
        tests = [
            test_session_start,
            test_session_start_skips_placeholder_templates,
            test_subagent_start_denies_missing_assignment,
            test_subagent_start_allows_with_assignment,
            test_auditor_denies_wrong_agent_logs,
            test_auditor_allows_assignee_lifecycle,
            test_auditor_accepts_legacy_system_delegation,
            test_subagent_stop_followup,
            test_subagent_stop_followup_implementer,
            test_log_task_delegation,
            test_log_task_result,
            test_log_agent_response_skips_non_factory,
            test_log_agent_response_logs_factory,
            test_view_messages_script,
            test_protect_done_milestones_allows_unprotected,
            test_protect_done_milestones_denies_hotfix_phrase,
            test_protect_done_milestones_allows_reopened_milestone,
            test_scope_parser_uses_structure_section_only,
            test_block_git_push_denies,
            test_block_git_push_allows_commit,
            test_block_git_push_denies_global_option,
            test_run_log_reports_failure,
            test_gitignore_sync_adds_detected_artifact_once,
            test_gitignore_sync_never_ignores_tracked_artifact,
        ]
        for test in tests:
            test()
    print(f"\n{len(tests)} hook tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
