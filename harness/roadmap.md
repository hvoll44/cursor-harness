# Roadmap

> How to achieve the [project vision](project-vision.md). The system agent tracks progress here and adjusts sequencing when blockers appear.

**Status legend:** `pending` · `in_progress` · `blocked` · `done` · `skipped`

## Current Phase

**Phase 1 — Playable browser prototype** — Architecture, core gameplay, and automated E2E verification.

## Milestones

| ID | Milestone | Owner | Status | Depends On | Notes |
|----|-----------|-------|--------|------------|-------|
| M1 | Architecture & project structure | architect | done | — | Architecture doc, ADR 0001, Vite scaffold |
| M2 | Core game implementation | implementer | done | M1 | Bugfix: S/Z SRS rotation shapes corrected |
| M3 | E2E test coverage | tester | pending | M2 | Browser tests for start, play, line clear, game over, restart |

## Active Assignments

| Assignment ID | Agent | Milestone | Status | Created |
|---------------|-------|-----------|--------|---------|
| _none_ | — | — | — | — |

## Blockers

_None._

## Adjustments Log

| Date | Change | Reason |
|------|--------|--------|
| 2026-06-29 | Initial roadmap | Browser Tetris-like game project kickoff |
| 2026-06-30 | Reopened M2 for bugfix | User report: green S piece wrong orientation when vertical |

## Completion Checklist

Before marking the project complete, the system agent verifies:

- [ ] All milestones are `done` or explicitly `skipped`
- [ ] [project-vision.md](project-vision.md) success criteria are met
- [ ] Auditor has signed off on final assignments
- [ ] E2E tests pass (tester)
