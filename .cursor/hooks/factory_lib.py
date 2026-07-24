"""Shared utilities for Software Development Factory Cursor hooks."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

FACTORY_AGENTS = frozenset({"system", "architect", "implementer", "tester", "auditor"})
FACTORY_SUBAGENT_TYPES = frozenset(
    {"architect", "implementer", "tester", "auditor", "system", "generalPurpose", "explore", "shell"}
)
ASSIGNMENT_ID_RE = re.compile(
    r"\b(architect|implementer|tester|auditor|system)-M\d+-\d+\b", re.IGNORECASE
)
ASSIGNMENT_PATH_RE = re.compile(r"factory/assignments/[\w-]+\.md", re.IGNORECASE)
MILESTONE_ID_RE = re.compile(r"\bM\d+\b")

# Always editable regardless of done-milestone protection
EXEMPT_PATH_PREFIXES = (
    "factory/",
    ".cursor/",
    ".git/",
)

LOG_SCRIPT = Path(__file__).resolve().parent.parent / "skills" / "factory-log" / "scripts" / "log-action.py"


def repo_root(hook_input: dict | None = None) -> Path:
    if hook_input:
        roots = hook_input.get("workspace_roots") or []
        if roots:
            return Path(roots[0])
    return Path(__file__).resolve().parents[2]


def emit(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def read_stdin_json() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    return json.loads(raw)


def detect_factory_agent(task: str, subagent_type: str = "") -> str | None:
    lowered = task.lower()
    agent_type = subagent_type.lower()
    if agent_type in FACTORY_AGENTS:
        return agent_type
    for agent in FACTORY_AGENTS:
        if re.search(rf"\b{agent}\b", lowered):
            return agent
        if f"/{agent}" in lowered:
            return agent
    return None


def parse_assignment_id(text: str) -> str | None:
    match = ASSIGNMENT_ID_RE.search(text)
    return match.group(0) if match else None


def has_assignment_context(text: str) -> bool:
    if ASSIGNMENT_PATH_RE.search(text):
        return True
    return parse_assignment_id(text) is not None


def assignment_path(root: Path, assignment_id: str) -> Path:
    return root / "factory" / "assignments" / f"{assignment_id}.md"


def read_assignment_status(path: Path) -> str | None:
    if not path.is_file():
        return None
    content = path.read_text(encoding="utf-8")
    match = re.search(r"\*\*Status\*\*\s*\|\s*`(\w+)`", content)
    return match.group(1).lower() if match else None


def read_assignment_milestone(path: Path) -> str | None:
    if not path.is_file():
        return None
    content = path.read_text(encoding="utf-8")
    match = re.search(r"\*\*Milestone\*\*\s*\|\s*`(\w+)`", content)
    return match.group(1) if match else None


def parse_milestone_statuses(root: Path) -> dict[str, str]:
    roadmap = root / "factory" / "roadmap.md"
    if not roadmap.is_file():
        return {}
    statuses: dict[str, str] = {}
    in_table = False
    for line in roadmap.read_text(encoding="utf-8").splitlines():
        if line.startswith("| ID |"):
            in_table = True
            continue
        if in_table:
            if not line.startswith("|"):
                in_table = False
                continue
            if line.startswith("|----"):
                continue
            parts = [p.strip() for p in line.strip("|").split("|")]
            if len(parts) >= 4 and parts[0].startswith("M"):
                statuses[parts[0]] = parts[3].strip("`").lower()
    return statuses


def load_milestone_paths(root: Path) -> dict[str, list[str]]:
    path = root / "factory" / "milestone-paths.json"
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    result: dict[str, list[str]] = {}
    for key, value in data.items():
        if key.startswith("_"):
            continue
        if isinstance(value, list):
            result[key] = [p.replace("\\", "/") for p in value]
    return result


def protected_paths_for_done_milestones(root: Path) -> list[str]:
    statuses = parse_milestone_statuses(root)
    paths_map = load_milestone_paths(root)
    protected: list[str] = []
    for milestone_id, status in statuses.items():
        if status != "done":
            continue
        protected.extend(paths_map.get(milestone_id, []))
    return protected


def normalize_rel_path(root: Path, file_path: str) -> str:
    p = Path(file_path)
    try:
        rel = p.resolve().relative_to(root.resolve())
    except ValueError:
        rel = p
    return rel.as_posix()


def is_exempt_path(rel_path: str) -> bool:
    return any(rel_path.startswith(prefix) for prefix in EXEMPT_PATH_PREFIXES)


def path_under_prefix(rel_path: str, prefix: str) -> bool:
    prefix = prefix.replace("\\", "/").strip("/")
    rel = rel_path.strip("/")
    if not prefix:
        return False
    return rel == prefix or rel.startswith(prefix + "/")


def is_protected_path(root: Path, file_path: str) -> tuple[bool, str | None]:
    rel = normalize_rel_path(root, file_path)
    if is_exempt_path(rel):
        return False, None
    for protected in protected_paths_for_done_milestones(root):
        if path_under_prefix(rel, protected):
            return True, protected
    return False, None


def parse_architecture_paths(root: Path) -> list[str]:
    arch = root / "docs" / "architecture.md"
    if not arch.is_file():
        return []
    content = arch.read_text(encoding="utf-8")
    paths: set[str] = set()
    in_structure = False
    for line in content.splitlines():
        if re.match(r"^#+\s*(folder\s+structure|directory\s+layout|project\s+structure)", line, re.I):
            in_structure = True
            continue
        if in_structure and re.match(r"^#+\s", line) and "structure" not in line.lower():
            in_structure = False
        candidates = re.findall(r"`([^`]+)`", line)
        candidates += re.findall(r"(?:├──|└──|[-*])\s+([^\s│]+)", line)
        for raw in candidates:
            cleaned = raw.strip().rstrip("/")
            if cleaned and not cleaned.startswith("http"):
                if "/" in cleaned or "." in cleaned:
                    paths.add(cleaned.replace("\\", "/"))
                else:
                    paths.add(cleaned.replace("\\", "/") + "/")
    return sorted(paths)


def is_in_scope(root: Path, file_path: str) -> tuple[bool, str | None]:
    rel = normalize_rel_path(root, file_path)
    if is_exempt_path(rel):
        return True, None
    allowed = parse_architecture_paths(root)
    if not allowed:
        return True, None
    for prefix in allowed:
        if path_under_prefix(rel, prefix):
            return True, None
    return False, rel


def assignment_has_logs(root: Path, assignment_id: str, *actions: str) -> bool:
    log_dir = root / "factory" / "log"
    if not log_dir.is_dir():
        return False
    required = set(actions)
    found: set[str] = set()
    for log_file in sorted(log_dir.glob("*.jsonl")):
        for line in log_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("assignment_id") == assignment_id:
                action = entry.get("action")
                if action in required:
                    found.add(action)
    return required.issubset(found)


def parse_tool_input(data: dict) -> dict:
    tool_input = data.get("tool_input") or {}
    if isinstance(tool_input, str):
        try:
            tool_input = json.loads(tool_input)
        except json.JSONDecodeError:
            tool_input = {}
    if not isinstance(tool_input, dict):
        return {}
    return tool_input


def infer_parent_agent(data: dict) -> str:
    agent_message = (data.get("agent_message") or "").lower()
    for agent in ("system", "architect", "implementer", "tester", "auditor"):
        if f"/{agent}" in agent_message or re.search(rf"\b{agent}\b", agent_message):
            return agent
    return "system"


def is_factory_task_subagent(subagent_type: str, prompt: str) -> bool:
    lowered = subagent_type.lower()
    if lowered in FACTORY_AGENTS:
        return True
    if detect_factory_agent(prompt, subagent_type):
        return True
    return bool(parse_assignment_id(prompt) or ASSIGNMENT_PATH_RE.search(prompt))


def run_log(
    root: Path,
    agent: str,
    action: str,
    summary: str,
    assignment_id: str = "",
    milestone: str = "",
    details: dict | None = None,
) -> None:
    cmd = [
        sys.executable,
        str(LOG_SCRIPT),
        "--agent",
        agent,
        "--action",
        action,
        "--summary",
        summary,
    ]
    if assignment_id:
        cmd.extend(["--assignment-id", assignment_id])
    if milestone:
        cmd.extend(["--milestone", milestone])
    if details:
        cmd.extend(["--details", json.dumps(details, ensure_ascii=False)])
    subprocess.run(
        cmd,
        cwd=root,
        check=False,
        capture_output=True,
        env={**os.environ, "FACTORY_ROOT": str(root)},
    )


def run_log_message(
    root: Path,
    *,
    agent: str,
    summary: str,
    from_agent: str,
    to_agent: str,
    kind: str,
    body: str,
    assignment_id: str = "",
    milestone: str = "",
    details: dict | None = None,
) -> None:
    cmd = [
        sys.executable,
        str(LOG_SCRIPT),
        "--agent",
        agent,
        "--action",
        "message",
        "--summary",
        summary,
        "--from-agent",
        from_agent,
        "--to-agent",
        to_agent,
        "--kind",
        kind,
        "--body",
        body,
    ]
    if assignment_id:
        cmd.extend(["--assignment-id", assignment_id])
    if milestone:
        cmd.extend(["--milestone", milestone])
    if details:
        cmd.extend(["--details", json.dumps(details, ensure_ascii=False)])
    subprocess.run(
        cmd,
        cwd=root,
        check=False,
        capture_output=True,
        env={**os.environ, "FACTORY_ROOT": str(root)},
    )


def read_roadmap_summary(root: Path) -> str:
    roadmap = root / "factory" / "roadmap.md"
    vision = root / "factory" / "project-vision.md"
    parts: list[str] = ["## Software Development Factory — Session Context"]

    if vision.is_file():
        vision_text = vision.read_text(encoding="utf-8")
        summary_match = re.search(
            r"## Summary\s*\n+([\s\S]*?)(?=\n## |\Z)", vision_text
        )
        if summary_match:
            parts.append("### Vision Summary\n" + summary_match.group(1).strip())

    if roadmap.is_file():
        content = roadmap.read_text(encoding="utf-8")
        phase = re.search(r"## Current Phase\s*\n+([\s\S]*?)(?=\n## |\Z)", content)
        if phase:
            parts.append("### Current Phase\n" + phase.group(1).strip())

        statuses = parse_milestone_statuses(root)
        if statuses:
            lines = ["### Milestones"]
            for mid, status in statuses.items():
                lines.append(f"- **{mid}**: `{status}`")
            parts.append("\n".join(lines))

        blockers = re.search(r"## Blockers\s*\n+([\s\S]*?)(?=\n## |\Z)", content)
        if blockers and "_None_" not in blockers.group(1):
            parts.append("### Blockers\n" + blockers.group(1).strip())

        active = re.search(
            r"## Active Assignments\s*\n+\|[\s\S]*?\n(\|[^\n]+\n)+", content
        )
        if active:
            rows = [
                r
                for r in active.group(0).splitlines()
                if r.startswith("|") and "_none_" not in r and "Assignment ID" not in r
            ]
            if rows:
                parts.append("### Active Assignments\n" + "\n".join(rows[1:]))

    return "\n\n".join(parts)
