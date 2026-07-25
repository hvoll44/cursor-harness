# Roadmap

> How to achieve the [project vision](project-vision.md). The system agent tracks progress here and adjusts sequencing when blockers appear.

**Status legend:** `pending` · `in_progress` · `blocked` · `done` · `skipped`

## Current Phase

Planning — the project vision is defined and M1 is ready for architectural
delegation.

## Milestones

| ID | Milestone | Owner | Status | Depends On | Notes |
|----|-----------|-------|--------|------------|-------|
| M1 | Architecture and application foundation | Architect | pending | — | Select the browser stack; document modules, game-state boundaries, test tooling, and GitHub Pages deployment approach. |
| M2 | Core Tetris game engine | Implementer | pending | M1 | Implement deterministic board, tetromino, movement, rotation, collision, line clearing, scoring, levels, and game-over logic with automated unit tests. |
| M3 | Responsive playable game experience | Implementer | pending | M1, M2 | Build the accessible game UI, start/pause/restart flows, score and next-piece panels, desktop keyboard input, and touch controls. |
| M4 | Static deployment and end-to-end coverage | Tester | pending | M2, M3 | Add a browser-level happy-path test, verify responsive behavior, and validate production builds and GitHub Pages deployment configuration. |
| M5 | Release audit and GitHub Pages launch | System | pending | M4 | Obtain final audit approval, enable the configured GitHub Pages workflow, and verify the published URL. |

## Active Assignments

| Assignment ID | Agent | Milestone | Status | Created |
|---------------|-------|-----------|--------|---------|
| _none_ | — | — | — | — |

## Blockers

_None._

## Adjustments Log

| Date | Change | Reason |
|------|--------|--------|
| 2026-07-25 | Created M1–M5 delivery sequence | Establishes architecture-first delivery, then game logic, player experience, validation, and release. |


## Completion Checklist

Before marking the project complete, the system agent verifies:

- [ ] All milestones are `done` or explicitly `skipped`
- [ ] [project-vision.md](project-vision.md) success criteria are met
- [ ] Auditor has signed off on final assignments
- [ ] E2E tests pass (tester)
