# Factory Hooks

Project hooks for the Software Development Factory. Configured in [hooks.json](../hooks.json).

## Requirements

- Python 3 on `PATH` (hooks invoke `python .cursor/hooks/*.py`)

## Hooks

### 1 — Auto-log subagent lifecycle

**Events:** `subagentStart`, `subagentStop`  
**Script:** `subagent_start.py`, `subagent_stop.py`

Detects factory agents (`foreman`, `architect`, `implementer`, `tester`, `auditor`) and appends entries to `factory/log/` via `log-action.py`.

### 2 — Require assignment context

**Event:** `subagentStart`  
**Script:** `subagent_start.py`

Denies `/architect`, `/implementer`, and `/tester` unless the task prompt includes:

- `factory/assignments/<id>.md`, or
- An assignment ID matching `implementer-M2-01` pattern

`/foreman` is exempt (it creates assignments).

### 3 — Chain auditor after specialist completes

**Event:** `subagentStop` (`loop_limit: 3`)  
**Script:** `subagent_stop.py`

When `architect`, `implementer`, or `tester` completes, returns a `followup_message` prompting the **factory-audit** checklist and `/auditor` invocation.

### 4 — Gate auditor invocation

**Event:** `subagentStart`  
**Script:** `subagent_start.py`

Denies `/auditor` unless:

- Assignment file exists with status `completed`
- `factory/log/` contains a `delegated` entry from `foreman`, plus `started` and
  `completed` entries from the assignment's declared specialist agent

### 5 — Inject session context

**Event:** `sessionStart`  
**Script:** `session_start.py`

Returns `additional_context` with vision summary, current phase, milestone statuses, blockers, and active assignments.

### 6 — Protect done milestones

**Event:** `preToolUse` (matcher: `Write|Delete|StrReplace`)  
**Script:** `protect_done_milestones.py`

Blocks file edits under path prefixes listed in `factory/milestone-paths.json` for milestones marked `done` in `factory/roadmap.md`.

Exempt paths: `factory/`, `.cursor/`, `.git/`

To reopen protected work, `/foreman` must move the milestone out of `done` in
`factory/roadmap.md`, log the adjustment, and delegate a rework assignment.

### 7 — Warn on out-of-scope edits

**Event:** `postToolUse` (matcher: `Write|StrReplace`)  
**Script:** `warn_out_of_scope.py`

After a write, injects `additional_context` if the file is outside paths declared in `docs/architecture.md` (Folder Structure section). No warning if architecture doc is missing.

### 8 — Block git push

**Event:** `beforeShellExecution` (matcher: `git push`, `failClosed: true`)  
**Script:** `block_git_push.py`

Blocks any `git push` command (including `git push origin`, `git push -u origin main`, `--force`, etc.). Local git operations such as `git add`, `git commit`, `git status`, and `git diff` remain allowed.

This is a workflow control, not a security boundary: Git aliases, wrappers, or
other tools that push without executing a detectable Git push command may not
be intercepted.

### 9 — Log agent messages

**Events:** `preToolUse` (`Task`), `postToolUse` (`Task`), `afterAgentResponse`  
**Scripts:** `log_task_delegation.py`, `log_task_result.py`, `log_agent_response.py`

Captures parent→subagent delegations, Task tool results, and factory-related assistant responses. Combined with subagent start/stop hooks, this builds a full conversation thread in `factory/log/`.

View messages:

```bash
python .cursor/skills/factory-log/scripts/view-messages.py
python .cursor/skills/factory-log/scripts/view-messages.py --assignment-id implementer-M2-01
```

Full bodies are stored under `factory/log/messages/YYYY-MM-DD/`.

### 10 — Synchronize generated-file ignores

**Events:** `sessionStart`, `afterFileEdit`, `afterShellExecution`
**Script:** `sync_gitignore.py`

Maintains `.gitignore` for a narrow, safe allowlist of generated artifacts:

- Python bytecode and caches: `__pycache__/`, `*.py[cod]`
- Test/type/lint output: `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `.coverage`, `htmlcov/`
- Factory runtime activity: `factory/log/`

The hook appends a missing pattern only after it finds the matching artifact and
verifies Git does not track it. It never removes or rewrites existing rules,
adds broad catch-all patterns, or ignores source and Cursor configuration.
Failures are fail-open so routine work is not blocked.

## Milestone path protection

When marking a milestone `done` in the roadmap, register its paths:

```json
{
  "M1": ["docs/architecture.md", "src/"],
  "M2": ["tests/e2e/"]
}
```

## Testing

From repo root:

```bash
python .cursor/hooks/test_hooks.py
```

Debug via Cursor **Hooks** output channel after triggering real agent events.
