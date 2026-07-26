---
name: factory-delegate
description: Create factory assignments and delegation prompts for architect, implementer, tester, or auditor subagents. Use when the Foreman delegates work while preserving parent context.
---

# Factory Delegate

Deterministic workflow for the **Foreman** to delegate work to specialists.

## Steps

### 1. Choose target and milestone

Pick subagent: `architect` | `implementer` | `tester` | `auditor`  
Pick roadmap milestone ID from [factory/roadmap.md](../../../factory/roadmap.md).

Delegate `implementer` only after architecture exists (`docs/architecture.md` or explicit structure in the assignment).

### 2. Generate assignment ID

Format: `{agent}-{milestone}-{seq}` — increment seq per agent+milestone (01, 02, …).

### 3. Create assignment file

Copy [factory/assignments/_template.md](../../../factory/assignments/_template.md) to:

```
factory/assignments/{assignment-id}.md
```

Replace placeholders:

- `{ASSIGNMENT_ID}` → assignment ID
- `{agent}` → target agent name
- `{milestone_id}` → milestone ID
- `{ISO8601}` → current UTC timestamp

Fill **Objective**, **Context from Foreman**, **Acceptance Criteria**, and **Deliverables**.

### 4. Update roadmap

In [factory/roadmap.md](../../../factory/roadmap.md):

- Add row to **Active Assignments**
- Set milestone status to `in_progress` if it was `pending`

### 5. Log delegation

```bash
python .cursor/skills/factory-log/scripts/log-action.py \
  --agent foreman \
  --action delegated \
  --assignment-id {assignment-id} \
  --milestone {milestone-id} \
  --summary "Delegated to {agent}: {one-line objective}"
```

Also log the delegation prompt as a message (or rely on the Task hook to capture it automatically when you invoke the subagent):

```bash
python .cursor/skills/factory-log/scripts/log-action.py \
  --agent foreman \
  --action message \
  --from-agent foreman \
  --to-agent {agent} \
  --kind delegation \
  --assignment-id {assignment-id} \
  --summary "Delegated to {agent}: {one-line objective}" \
  --body "{full delegation prompt pasted below}"
```

### 6. Invoke subagent

Use explicit invocation with the assignment path and pasted **Context from Foreman**:

```
/{agent}

Assignment: factory/assignments/{assignment-id}.md

[Paste Context from Foreman section here]

Acceptance criteria:
[Paste criteria here]
```

For **auditor**, invoke only after assignee marked assignment `completed`.

### 7. After subagent returns

- Update assignment **Status** in the file
- Remove or update **Active Assignments** row in roadmap
- If auditor passed, set milestone to `done` and log `milestone_updated`
- If auditor failed, create a new assignment with incremented seq for rework

## Delegation prompt template

```markdown
You are working assignment `{assignment-id}` for milestone `{milestone-id}`.

Read the full assignment: factory/assignments/{assignment-id}.md

Objective: {objective}

Vision constraints (from project-vision):
- {bullet}

Deliverables:
- {bullet}

Acceptance criteria:
- {bullet}

Log started/completed via factory-log skill.
```
