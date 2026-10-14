---
name: web-game-stack
description: Build or extend a browser game with the shared ALS and Blacksite stack. Use for new TPP or FPP games, multiplayer, character control, weapons, console input, asset loading, or deployment.
---

# Web game stack

Last verified: 2026-10-13.

## Start a game

1. Pick `tpp`, `fpp`, or `blank` using [profiles](references/profiles.md). TPP is vanilla ALS shoulder camera. FPP adds an arms-only first-person view, Operator, Arsenal, and a Controller → Pawn → Intent seam.
2. Inspect `node scripts/scaffold.mjs catalog --json` for profiles and optional systems. Run `node scripts/scaffold.mjs --profile tpp|fpp|blank --name "Display name" --dir /absolute/path --systems operator,arsenal,warden,rupture --json --gate`. Omit optional systems instead of passing an empty string. The CLI is noninteractive and emits NDJSON. On Windows use an absolute drive path and Node installed through Volta.
3. The generated repo holds Blacksite and als-web as Git submodules. It uses package source exports, lists selected Blacksite packages and their workspace dependencies only, and serves ALS's own public assets directly. Run `pnpm dev` after the gate. The starter is an arena, not a finished game; add content and authority deliberately.
4. For multiplayer, add the client/server protocol and authority described in [netcode](references/netcode-colyseus.md) before combat becomes network dependent. Keep the offline authority callable by both server and local range.
5. Run `pnpm check` (lint, typecheck, build) after changes and playtest the interaction in a real browser before release.

## Invariants

- Koota owns entity identity and continuous gameplay data; XState owns discrete transitions; Effect owns services, decoding, retries, streams, and resource lifetimes. Colyseus transports projections of authority state. See [state](references/state-effect-xstate-koota.md).
- Clients author and predict their movement. The server validates hits, damage, teams, life, inventory, and score. Movement limits and rewound target capsules bound client claims.
- Game source has no comments or test files under the included oxlint rules. Shared Blacksite packages retain a focused invariant and public-contract test suite.
- Game UI uses spatial console navigation, gamepad and keyboard parity, 44 px targets, and no browser tab-order or focus outlines as its primary game navigation.
- Keep purchased content in ignored local directories. Read no credential files. Move only converters and format contracts into shared code.
- Dependencies use latest published caret ranges when generated. The [exception record](references/pins-and-exceptions.md) identifies the patched Rupture Rapier build. Update the skill after a proven improvement using [update procedure](references/update-procedure.md).

## Read on demand

| Concern | Reference |
| --- | --- |
| Profile and system choice | [profiles](references/profiles.md) |
| Effect, XState, Koota | [state](references/state-effect-xstate-koota.md) |
| Colyseus and hit validation | [netcode](references/netcode-colyseus.md) |
| Possession and FPP intent | [controller-intent](references/controller-intent.md) |
| ALS and submodules | [als-integration](references/als-integration.md) |
| R3F and Rapier | [rendering-physics](references/rendering-physics.md) |
| Console UI and input | [ui-and-input](references/ui-and-input.md) |
| Owned content | [assets-pipeline](references/assets-pipeline.md) |
| Loading | [loading-warmup](references/loading-warmup.md) |
| VFX and audio | [vfx-audio](references/vfx-audio.md) |
| Shipping | [deploy](references/deploy.md) |
| Gates and conventions | [gate-and-conventions](references/gate-and-conventions.md) |

Templates in `assets/` contain the three starter profiles, lint plugin, warmup registry, workspace, and deployment skeletons. `scripts/check-skill.mjs` checks the published skill's structure and dependency-range policy.
