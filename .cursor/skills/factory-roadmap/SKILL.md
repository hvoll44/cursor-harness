---
name: factory-roadmap
description: Update Software Development Factory roadmap milestone and assignment status. Use when milestones progress, block, complete, or get re-sequenced.
---

# Factory Roadmap

Deterministic updates to [factory/roadmap.md](../../../factory/roadmap.md).

## Read first

Always read current roadmap and [factory/project-vision.md](../../../factory/project-vision.md) before editing.

## Update milestone status

In the **Milestones** table, set **Status** to one of:

| Status | Meaning |
|--------|---------|
| `pending` | Not started |
| `in_progress` | Active assignment exists |
| `blocked` | Waiting on external dependency or failed audit |
| `done` | Auditor passed; deliverables verified |
| `skipped` | Foreman explicitly descoped with reason in Notes |

After changing status, log:

```bash
python .cursor/skills/factory-log/scripts/log-action.py \
  --agent foreman \
  --action milestone_updated \
  --milestone M2 \
  --summary "M2 set to in_progress"
```

## Active assignments table

| Event | Action |
|-------|--------|
| Delegate | Add row with assignment ID, agent, milestone, `in_progress`, date |
| Complete + audit pass | Remove row or mark done |
| Audit fail | Keep row; set status `blocked` on milestone |

## Blockers section

When status is `blocked`, add an entry:

```markdown
- **M2** — {reason} — since {date}
```

Clear the entry when unblocked.

## Adjustments log

When re-sequencing or changing scope, append a row:

```markdown
| 2026-06-29 | Moved M3 before M2 | E2E framework needed earlier |
```

Log with `--action adjusted`.

## Completion

Only mark project complete when **Completion Checklist** in roadmap can be checked off. Requires all milestones `done` or `skipped`, vision criteria met, and final auditor pass.

When setting a milestone to `done`, update [factory/milestone-paths.json](../../../factory/milestone-paths.json) with path prefixes to protect via hooks.
