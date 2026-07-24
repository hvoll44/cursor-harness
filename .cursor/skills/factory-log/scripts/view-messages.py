#!/usr/bin/env python3
"""Render factory agent message logs as a readable conversation thread."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

KIND_LABELS = {
    "delegation": "Delegation",
    "prompt": "Prompt",
    "response": "Response",
    "followup": "Follow-up",
    "tool_result": "Task result",
    "assistant": "Assistant",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def log_dir() -> Path:
    return repo_root() / "factory" / "log"


def read_body(entry: dict) -> str:
    details = entry.get("details") or {}
    if not isinstance(details, dict):
        return details.get("body_preview", "") if isinstance(details, str) else str(details)

    body_ref = details.get("body_ref")
    if body_ref:
        path = log_dir() / body_ref
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            return re.sub(r"^<!--.*?-->\n\n", "", text, count=1, flags=re.S).strip()

    return str(details.get("body_preview") or "")


def load_entries(*, date: str | None, assignment_id: str | None) -> list[dict]:
    root = log_dir()
    if not root.is_dir():
        return []

    files: list[Path]
    if date:
        candidate = root / f"{date}.jsonl"
        files = [candidate] if candidate.is_file() else []
    else:
        files = sorted(root.glob("*.jsonl"))

    entries: list[dict] = []
    for path in files:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if assignment_id and entry.get("assignment_id") != assignment_id:
                continue
            entries.append(entry)
    entries.sort(key=lambda e: e.get("timestamp", ""))
    return entries


def format_timestamp(ts: str) -> str:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%H:%M:%S")
    except ValueError:
        return ts[:19] if ts else "?"


def render_entry(entry: dict, *, show_actions: bool, show_meta: bool) -> list[str]:
    action = entry.get("action", "")
    if action == "message" or (show_actions and action):
        lines: list[str] = []
        ts = format_timestamp(entry.get("timestamp", ""))
        if action == "message":
            details = entry.get("details") or {}
            kind = details.get("kind", "message")
            label = KIND_LABELS.get(kind, kind)
            sender = details.get("from", entry.get("agent", "?"))
            recipient = details.get("to", "?")
            header = f"[{ts}] {label}: {sender} -> {recipient}"
            if entry.get("assignment_id"):
                header += f" ({entry['assignment_id']})"
            lines.append(header)
            lines.append(f"  {entry.get('summary', '')}")
            body = read_body(entry)
            if body:
                for body_line in body.splitlines():
                    lines.append(f"  | {body_line}")
            if show_meta and isinstance(details, dict):
                meta = {
                    k: v
                    for k, v in details.items()
                    if k not in {"kind", "from", "to", "body_ref", "body_preview"}
                }
                if meta:
                    lines.append(f"  meta: {json.dumps(meta, ensure_ascii=False)}")
        elif show_actions:
            header = f"[{ts}] {action}: {entry.get('agent', '?')}"
            if entry.get("assignment_id"):
                header += f" ({entry['assignment_id']})"
            lines.append(header)
            lines.append(f"  {entry.get('summary', '')}")
        lines.append("")
        return lines
    return []


def render_conversation(entries: list[dict], *, show_actions: bool, show_meta: bool) -> str:
    lines: list[str] = []
    messages = [e for e in entries if e.get("action") == "message"]
    actions = [e for e in entries if e.get("action") != "message"]

    lines.append("# Factory conversation log")
    lines.append("")
    lines.append(f"Messages: {len(messages)} | Actions: {len(actions)}")
    lines.append("")

    if messages:
        lines.append("## Messages")
        lines.append("")
        for entry in messages:
            lines.extend(render_entry(entry, show_actions=False, show_meta=show_meta))

    if show_actions and actions:
        lines.append("## Actions")
        lines.append("")
        for entry in actions:
            lines.extend(render_entry(entry, show_actions=True, show_meta=show_meta))

    return "\n".join(lines).rstrip() + "\n"


def render_by_assignment(entries: list[dict], *, show_actions: bool, show_meta: bool) -> str:
    grouped: dict[str, list[dict]] = defaultdict(list)
    unassigned: list[dict] = []
    for entry in entries:
        aid = entry.get("assignment_id")
        if aid:
            grouped[aid].append(entry)
        else:
            unassigned.append(entry)

    lines = ["# Factory conversation log (by assignment)", ""]
    for aid in sorted(grouped):
        lines.append(f"## {aid}")
        lines.append("")
        for entry in grouped[aid]:
            lines.extend(render_entry(entry, show_actions=show_actions, show_meta=show_meta))

    if unassigned:
        lines.append("## (no assignment)")
        lines.append("")
        for entry in unassigned:
            lines.extend(render_entry(entry, show_actions=show_actions, show_meta=show_meta))

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="View factory agent message logs")
    parser.add_argument("--date", help="Filter to YYYY-MM-DD log file")
    parser.add_argument("--assignment-id", help="Filter to one assignment ID")
    parser.add_argument(
        "--by-assignment",
        action="store_true",
        help="Group output by assignment ID",
    )
    parser.add_argument(
        "--include-actions",
        action="store_true",
        help="Include non-message action entries (started, completed, etc.)",
    )
    parser.add_argument(
        "--meta",
        action="store_true",
        help="Show correlation metadata (conversation_id, subagent_id, etc.)",
    )
    parser.add_argument(
        "--messages-only",
        action="store_true",
        help="Only show message entries (default when neither flag is set)",
    )
    args = parser.parse_args()

    entries = load_entries(date=args.date, assignment_id=args.assignment_id)
    if not entries:
        print("No log entries found.", file=sys.stderr)
        return 1

    if not args.include_actions:
        message_entries = [e for e in entries if e.get("action") == "message"]
        if message_entries:
            entries = message_entries

    if args.by_assignment:
        output = render_by_assignment(
            entries,
            show_actions=args.include_actions,
            show_meta=args.meta,
        )
    else:
        output = render_conversation(
            entries,
            show_actions=args.include_actions,
            show_meta=args.meta,
        )

    sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
