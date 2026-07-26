---
name: factory-log
description: Append structured action entries to factory/log for Software Development Factory agents. Use when starting, completing, delegating, blocking, or adjusting factory work. All factory agents must log their actions.
---

# Factory Log

Deterministic logging for the Software Development Factory. Every agent logs significant actions.

## Run the script

From the repository root:

```bash
python .cursor/skills/factory-log/scripts/log-action.py \
  --agent architect \
  --action started \
  --assignment-id architect-M2-01 \
  --milestone M2 \
  --summary "Designing module layout for API layer"
```

```powershell
python .cursor/skills/factory-log/scripts/log-action.py `
  --agent foreman `
  --action delegated `
  --assignment-id architect-M2-01 `
  --milestone M2 `
  --summary "Delegated folder structure to architect"
```

## Parameters

| Flag | Required | Values |
|------|----------|--------|
| `--agent` | yes | `foreman`, `architect`, `implementer`, `tester`, `auditor`, `user` |
| `--action` | yes | `started`, `completed`, `delegated`, `blocked`, `adjusted`, `milestone_updated`, `audited`, `note`, `message` |
| `--summary` | yes | One-line description |
| `--assignment-id` | no | e.g. `architect-M2-01` |
| `--milestone` | no | e.g. `M2` |
| `--details` | no | Plain text or JSON object string |
| `--from-agent` | no | Message sender (with `--action message`) |
| `--to-agent` | no | Message recipient (with `--action message`) |
| `--kind` | no | `delegation`, `prompt`, `response`, `followup`, `tool_result`, `assistant` |
| `--body` | no | Full message text (stored under `factory/log/messages/`) |
| `--body-file` | no | Read message body from a file |
| `--body-ref` | no | Reference an existing stored body (skip writing) |

## Message logging

Use `--action message` to record agent-to-agent communication. Full bodies are stored in `factory/log/messages/YYYY-MM-DD/`; the JSONL entry holds metadata plus a preview.

```powershell
python .cursor/skills/factory-log/scripts/log-action.py `
  --agent foreman `
  --action message `
  --from-agent foreman `
  --to-agent architect `
  --kind delegation `
  --assignment-id architect-M3-01 `
  --summary "Delegated E2E test design to architect" `
  --body "Assignment: factory/assignments/architect-M3-01.md ..."
```

### View messages

```powershell
python .cursor/skills/factory-log/scripts/view-messages.py
python .cursor/skills/factory-log/scripts/view-messages.py --assignment-id implementer-M2-01
python .cursor/skills/factory-log/scripts/view-messages.py --date 2026-06-30 --by-assignment --meta
```

Hooks auto-log:

- **Task delegation** (`preToolUse` / `Task`) — parent prompt to subagent
- **Subagent prompt** (`subagentStart`) — full task text + correlation IDs
- **Subagent response** (`subagentStop`) — subagent summary + transcript path
- **Auditor follow-up** (`subagentStop`) — hook follow-up message to parent
- **Task result** (`postToolUse` / `Task`) — tool output returned to parent
- **Assistant** (`afterAgentResponse`) — factory-related parent responses

## Output

Appends one JSON line to `factory/log/YYYY-MM-DD.jsonl` and prints the path and entry.

## When to log

| Action | Who | Example |
|--------|-----|---------|
| `started` | assignee | Beginning an assignment |
| `completed` | assignee | Finished deliverables |
| `delegated` | foreman | Spawned a subagent |
| `blocked` | any | Cannot proceed — include reason in `--details` |
| `adjusted` | foreman | Roadmap re-sequenced |
| `milestone_updated` | foreman | Milestone status changed |
| `audited` | auditor | Verdict recorded |
| `note` | any | Informational |
| `message` | any | Agent-to-agent message (use `--body`, `--from-agent`, `--to-agent`, `--kind`) |

## Rules

- Log **before** claiming work complete (`completed` must exist for auditor)
- Include `--assignment-id` whenever work ties to an assignment
- Do not edit or delete log files — append only
