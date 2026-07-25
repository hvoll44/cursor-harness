# Project Vision

> What the end result should look like. The system agent reads this before delegating work and uses it to judge whether the project is on track.

## Summary

Build a polished, single-player Tetris game that runs entirely in a web
browser and is published as a static site through GitHub Pages. Players should
be able to start playing immediately without an account, installation, or
backend service.

## Success Criteria

What must be true when the project is done:

- A deployed GitHub Pages URL serves the game and loads correctly in a current
  desktop or mobile browser.
- The game implements the seven standard tetrominoes, rotation, lateral
  movement, soft drop, hard drop, line clearing, scoring, increasing speed,
  game over, and restart.
- A player can use keyboard controls on desktop and visible touch controls on
  small-screen devices.
- The game clearly communicates score, level, lines cleared, the next piece,
  controls, pause state, and game-over state.
- The application is usable without a network connection after its static
  assets have loaded and does not require any server-side API, authentication,
  or database.
- The production build is reproducible from the repository and is configured
  for deployment to GitHub Pages.

## User Experience

The game opens to a lightweight start screen with concise instructions and a
prominent Play button. During play, controls must feel responsive and the board
must remain readable at typical laptop and phone sizes. Pause and restart must
be discoverable without refreshing the page. A game-over screen must show the
final score and offer a one-click replay.


### Visual design

- Use a clean, arcade-inspired presentation: a high-contrast board, distinct
  colors for each tetromino, and restrained animation for movement and line
  clears.
- Keep the playfield as the visual focus, with score and next-piece panels
  arranged alongside it on wide displays and stacked accessibly on narrow
  displays.
- Support keyboard focus and use sufficient color contrast; do not rely on
  color alone to communicate an important game state.


## Technical Constraints

- Deliver a client-side static web application compatible with GitHub Pages;
  use no runtime server or server-side rendering.
- Choose a maintainable browser-oriented stack and include the required build
  and GitHub Pages deployment configuration in the repository.
- Ensure all deployed asset paths work under a GitHub Pages project-site base
  path, not only at a domain root.
- Implement deterministic, testable game-state logic separated from rendering
  where practical.
- Target current versions of Chrome, Edge, Firefox, and Safari, with a
  responsive layout for touch-capable screens.
- Include automated checks for the core game rules and an end-to-end happy-path
  test that starts and restarts a game.


## Out of Scope

- Multiplayer, online leaderboards, user accounts, and cloud-saved progress.
- Monetization, advertising, analytics, and social sharing.
- A native mobile or desktop application.
- Variants beyond the standard single-player Tetris rules unless added in a
  later milestone.


## References

- GitHub Pages documentation: <https://docs.github.com/pages>
- Tetris Guideline overview: <https://tetris.wiki/Tetris_Guideline>

