# Software Development Factory

A Cursor-native framework for orchestrating AI agents like a software development factory.

## What you get

- **System agent** — High-level overseer that delegates work and preserves its own context
- **Specialist agents** — Architect, Implementer, Tester, and Auditor with focused responsibilities
- **Living artifacts** — Project vision, roadmap, assignments, and action logs
- **Deterministic skills** — Logging, delegation, roadmap updates, and audit checklists
- **Automation hooks** — Enforce delegation, logging, auditor gating, and scope protection

## Getting started

1. Clone this repo into your project (or use it as a template)
2. Fill in [factory/project-vision.md](factory/project-vision.md) — describe what "done" looks like
3. Define milestones in [factory/roadmap.md](factory/roadmap.md)
4. Open Cursor Agent and run:

   ```
   /system

   Read factory/project-vision.md and factory/roadmap.md.
   Delegate the first milestone to the appropriate specialist.
   ```

## Directory layout

```
your-project/
├── AGENTS.md                 # Factory overview for any AI agent
├── factory/
│   ├── project-vision.md     # End-state definition
│   ├── roadmap.md            # Milestones and progress
│   ├── assignments/          # Per-task work packages
│   ├── log/                  # Daily JSONL action logs
│   └── milestone-paths.json  # Paths locked when milestones are done
└── .cursor/
    ├── hooks.json            # Factory automation hooks
    ├── hooks/                # Hook scripts (Python)
    ├── agents/               # Subagent definitions
    │   ├── system.md
    │   ├── architect.md
    │   ├── implementer.md
    │   ├── tester.md
    │   └── auditor.md
    ├── rules/
    │   └── factory-workspace.mdc
    └── skills/
        ├── factory-log/
        ├── factory-delegate/
        ├── factory-roadmap/
        └── factory-audit/
```

## Agent roles

| Agent | Responsibility |
|-------|----------------|
| **System** | Tracks roadmap, delegates to specialists, adjusts plan |
| **Architect** | System design and folder structure |
| **Implementer** | Application code and features |
| **Tester** | End-to-end test creation and execution |
| **Auditor** | Skeptical verification that work is actually complete |

## Typical flow

```
Vision + Roadmap
      ↓
   /system  ──delegates──→  /architect  (design)
      │                         ↓
      │                    /auditor  (verify)
      │                         ↓
      ├──delegates──→  /implementer  (build)
      │                         ↓
      │                    /auditor  (verify)
      │                         ↓
      ├──delegates──→  /tester  (e2e tests)
      │                         ↓
      │                    /auditor  (verify)
      ↓
  Milestone done → next milestone
```

## Logging

Every agent logs via the **factory-log** skill:

```powershell
python .cursor/skills/factory-log/scripts/log-action.py `
  --agent architect `
  --action completed `
  --assignment-id architect-M1-01 `
  --summary "Created docs/architecture.md and src layout"
```

### Agent messages

Hooks capture prompts, responses, and follow-ups between agents automatically. View the conversation thread:

```powershell
python .cursor/skills/factory-log/scripts/view-messages.py
python .cursor/skills/factory-log/scripts/view-messages.py --assignment-id implementer-M2-01 --include-actions
```

Full message bodies live in `factory/log/messages/YYYY-MM-DD/`. JSONL entries reference them via `details.body_ref`.

## Hooks

Project hooks in [.cursor/hooks.json](.cursor/hooks.json) automate factory enforcement:

| Hook | Event | Behavior |
|------|-------|----------|
| Auto-log subagents | `subagentStart` / `subagentStop` | Appends lifecycle + message entries to `factory/log/` |
| Log Task delegations | `preToolUse` / `Task` | Records parent→subagent delegation prompts |
| Log Task results | `postToolUse` / `Task` | Records subagent tool output returned to parent |
| Log assistant replies | `afterAgentResponse` | Records factory-related parent agent responses |
| Require assignment | `subagentStart` | Blocks `/architect`, `/implementer`, and `/tester` without assignment context |
| Gate auditor | `subagentStart` | Blocks `/auditor` unless assignment is `completed` with logs |
| Chain auditor | `subagentStop` | Follow-up to run `/auditor` after architect/implementer/tester completes |
| Session context | `sessionStart` | Injects vision summary and roadmap milestones |
| Protect done work | `preToolUse` | Blocks edits to paths under `done` milestones |
| Scope warning | `postToolUse` | Warns when edits fall outside `docs/architecture.md` structure |

When a milestone is marked `done`, add its path prefixes to [factory/milestone-paths.json](factory/milestone-paths.json).

Test hooks: `python .cursor/hooks/test_hooks.py`

## Learn more

See [AGENTS.md](AGENTS.md) for the full agent reference and workflow details.
