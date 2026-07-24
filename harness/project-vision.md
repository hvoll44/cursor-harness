# Project Vision

> What the end result should look like. The system agent reads this before delegating work and uses it to judge whether the project is on track.

## Summary

A browser-based falling-block puzzle game inspired by Tetris. Players control tetrominoes on a vertical grid, clear full horizontal lines to score points, and survive as drop speed increases with level. The game runs entirely in the browser with no install step — open a local or hosted HTML page and play with keyboard controls.

## Success Criteria

What must be true when the project is done:

- [ ] A playable game loads in a modern browser (Chrome, Firefox, Edge) from static files or a simple dev server
- [ ] All seven standard tetromino shapes spawn, rotate, move left/right, soft-drop, and hard-drop
- [ ] Completed horizontal lines are cleared; remaining blocks fall; score and level update correctly
- [ ] Game ends when new pieces cannot spawn; player can start a new game
- [ ] Controls are documented and work: arrow keys (move/rotate), space or down (hard/soft drop), optional pause
- [ ] UI shows score, level, lines cleared, and next-piece preview
- [ ] E2E tests verify core gameplay flows (start, move piece, clear line, game over)

## User Experience

### Play flow

1. User opens the game in a browser
2. A title screen or immediate playfield appears with score/level at 0
3. A random tetromino spawns at the top of a visible grid (typically 10×20 visible cells)
4. Player uses keyboard to position and rotate the piece before it locks
5. When a row is full, it disappears; score increases; after enough lines, level rises and pieces fall faster
6. When the stack blocks the spawn area, game over is shown with final score; player can restart

### Visual design

- Clean, readable grid with distinct colors per tetromino type
- Minimal chrome: playfield, score panel, next piece, game-over overlay
- Responsive enough to play on a laptop viewport (desktop-first; mobile optional)

### Controls (default)

| Key | Action |
|-----|--------|
| ← / → | Move piece left / right |
| ↑ | Rotate clockwise |
| ↓ | Soft drop (faster fall while held) |
| Space | Hard drop (instant lock) |
| P or Escape | Pause / resume |

## Technical Constraints

- **Platform:** Browser only; no native app or backend required for v1
- **Stack:** Vanilla HTML, CSS, and JavaScript (ES modules). No framework required; architect may choose a minimal bundler (e.g. Vite) if it simplifies structure
- **Rendering:** Canvas 2D or DOM grid — architect decides in M1
- **State:** Single-player, client-side only; no accounts or persistence beyond optional `localStorage` high score
- **Performance:** Smooth at 60fps on typical hardware; game loop via `requestAnimationFrame`
- **Accessibility:** Keyboard-only play is sufficient for v1; ARIA labels on score/UI elements where practical

## Out of Scope

- Multiplayer, online leaderboards, or user accounts
- Mobile touch controls (may be added later)
- Custom piece sets, battle modes, or non-standard Tetris variants
- Sound effects and music (nice-to-have; not required for v1)
- Packaging as desktop/mobile app (PWA, Electron, etc.)
- Licensing or branding as official Tetris™ — this is a Tetris-*like* clone for learning/demo purposes

## References

- [Tetris Guideline](https://tetris.fandom.com/wiki/Tetris_Guideline) — SRS rotation, 10×20 field, standard scoring concepts
- [tetris.wiki](https://tetris.wiki/) — grid sizes, piece definitions, line-clear mechanics
