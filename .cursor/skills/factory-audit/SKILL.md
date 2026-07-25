---
name: factory-audit
description: Pre-audit checklist before invoking the auditor subagent. Use when an assignment is claimed complete and needs verification before milestone closure.
---

# Factory Audit

Run this checklist **before** invoking `/auditor` to avoid wasted audit cycles.

## Preconditions

Assignment file exists at `factory/assignments/{id}.md` with:

- [ ] **Status** set to `completed` by assignee
- [ ] All **Deliverables** listed and present on disk
- [ ] System logged `delegated`, and the declared assignee logged `started` and
  `completed`, in `factory/log/`

## Quick self-check (system agent)

| Assignee | Verify |
|----------|--------|
| architect | Architecture doc exists; folders match doc; ADRs if required |
| implementer | Code at declared paths; build/run succeeds; matches acceptance criteria |
| tester | E2e tests exist; assignee reported pass count |
| any | Changes align with project-vision constraints |

## Invoke auditor

```
/auditor

Assignment: factory/assignments/{assignment-id}.md

Verify all acceptance criteria. Run tests if this is a tester assignment.
Return pass/fail with evidence.
```

## After verdict

| Verdict | System action |
|---------|---------------|
| `pass` | Update milestone to `done` via **factory-roadmap** skill |
| `fail` | Set milestone `blocked`; delegate rework with new assignment ID |

Log auditor outcome:

```bash
python .cursor/skills/factory-log/scripts/log-action.py \
  --agent auditor \
  --action audited \
  --assignment-id {id} \
  --summary "Verdict: pass|fail — {one line}"
```

## Rule

Never mark a roadmap milestone `done` without auditor `pass` recorded in the assignment file.
