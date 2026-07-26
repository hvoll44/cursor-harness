#!/usr/bin/env python3
"""Append a structured log entry to the Software Development Factory log."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

VALID_AGENTS = {"foreman", "architect", "implementer", "tester", "auditor", "user", "hook"}
VALID_ACTIONS = {
    "started",
    "completed",
    "delegated",
    "blocked",
    "adjusted",
    "milestone_updated",
    "audited",
    "note",
    "message",
}
VALID_MESSAGE_KINDS = {
    "delegation",
    "prompt",
    "response",
    "followup",
    "tool_result",
    "assistant",
}


def repo_root() -> Path:
    """Resolve repo root from script location: .cursor/skills/factory-log/scripts/"""
    configured_root = os.environ.get("FACTORY_ROOT")
    if configured_root:
        return Path(configured_root).resolve()
    return Path(__file__).resolve().parents[4]


def log_dir() -> Path:
    d = repo_root() / "factory" / "log"
    d.mkdir(parents=True, exist_ok=True)
    return d


def messages_dir(when: datetime) -> Path:
    d = log_dir() / "messages" / when.strftime("%Y-%m-%d")
    d.mkdir(parents=True, exist_ok=True)
    return d


def daily_log_path(when: datetime) -> Path:
    return log_dir() / f"{when.strftime('%Y-%m-%d')}.jsonl"


def update_log_index(when: datetime) -> Path:
    """Publish the JSONL filenames that the static Crew viewer can load."""
    directory = log_dir()
    logs = sorted(
        path.name for path in directory.glob("*.jsonl") if path.name != "index.json"
    )
    index = {
        "generated_at": when.isoformat(),
        "logs": logs,
    }
    path = directory / "index.json"
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
    return path


def preview(text: str, limit: int = 240) -> str:
    collapsed = re.sub(r"\s+", " ", text.strip())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 1] + "…"


def slug(text: str, limit: int = 40) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return (cleaned[:limit] or "message")


def store_body(when: datetime, body: str, *, from_agent: str, to_agent: str, kind: str) -> str:
    """Write full message body; return path relative to factory/log/."""
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()[:10]
    stamp = when.strftime("%H%M%S")
    filename = f"{stamp}-{slug(from_agent)}-to-{slug(to_agent)}-{slug(kind)}-{digest}.md"
    path = messages_dir(when) / filename
    header = (
        f"<!-- factory message: {kind} | {from_agent} -> {to_agent} | {when.isoformat()} -->\n\n"
    )
    path.write_text(header + body.strip() + "\n", encoding="utf-8")
    return path.relative_to(log_dir()).as_posix()


def parse_details(raw: str) -> dict | str:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    return raw


def main() -> int:
    parser = argparse.ArgumentParser(description="Log a factory agent action")
    parser.add_argument("--agent", required=True, choices=sorted(VALID_AGENTS))
    parser.add_argument("--action", required=True, choices=sorted(VALID_ACTIONS))
    parser.add_argument("--assignment-id", default="", help="Assignment ID if applicable")
    parser.add_argument("--milestone", default="", help="Roadmap milestone ID if applicable")
    parser.add_argument("--summary", required=True, help="One-line summary")
    parser.add_argument(
        "--details",
        default="",
        help="Optional extra detail (JSON object string or plain text)",
    )
    parser.add_argument("--from-agent", default="", help="Message sender (for action=message)")
    parser.add_argument("--to-agent", default="", help="Message recipient (for action=message)")
    parser.add_argument(
        "--kind",
        default="",
        choices=[""] + sorted(VALID_MESSAGE_KINDS),
        help="Message kind (for action=message)",
    )
    parser.add_argument("--body", default="", help="Full message body text to store")
    parser.add_argument("--body-file", default="", help="Read message body from a file")
    parser.add_argument(
        "--body-ref",
        default="",
        help="Existing body path relative to factory/log/ (skip writing body)",
    )
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    entry: dict[str, object] = {
        "timestamp": now.isoformat(),
        "agent": args.agent,
        "action": args.action,
        "summary": args.summary,
    }
    if args.assignment_id:
        entry["assignment_id"] = args.assignment_id
    if args.milestone:
        entry["milestone"] = args.milestone

    details = parse_details(args.details)
    if not isinstance(details, dict):
        details = {"note": details}

    if args.action == "message":
        from_agent = args.from_agent or args.agent
        to_agent = args.to_agent or "unknown"
        kind = args.kind or "prompt"
        body = args.body
        if args.body_file:
            body = Path(args.body_file).read_text(encoding="utf-8")
        body_ref = args.body_ref
        if body and not body_ref:
            body_ref = store_body(
                now,
                body,
                from_agent=from_agent,
                to_agent=to_agent,
                kind=kind,
            )
        message_details = {
            "kind": kind,
            "from": from_agent,
            "to": to_agent,
            **details,
        }
        if body_ref:
            message_details["body_ref"] = body_ref
        if body:
            message_details["body_preview"] = preview(body)
        elif body_ref:
            body_path = log_dir() / body_ref
            if body_path.is_file():
                stored = body_path.read_text(encoding="utf-8")
                stored = re.sub(r"^<!--.*?-->\n\n", "", stored, count=1, flags=re.S)
                message_details["body_preview"] = preview(stored)
        entry["details"] = message_details
    elif args.details:
        entry["details"] = details

    line = json.dumps(entry, ensure_ascii=False)
    path = daily_log_path(now)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    update_log_index(now)

    print(path)
    print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
