# Profiles and system choice

| Profile | Player | Camera | Included systems | Use when |
| --- | --- | --- | --- | --- |
| `tpp` | ALS local character and capsule | Native ALS third-person shoulder camera | ALS | A third-person game needs walking and animation first. |
| `fpp` | ALS body and capsule through Operator | Arms-only first-person view; V swaps to ALS third person | Operator, Arsenal, ALS | The game needs aiming and weapons from the first playable build. |
| `blank` | No character | Fixed R3F camera | ALS submodule available but unused | A simulation or custom controller will be added later. |

`--systems` adds optional Blacksite packages. `warden` is squad AI; `rupture` is destruction. The CLI reads their package manifests to include transitive `@blacksite/*` workspace dependencies. Do not add every Blacksite package glob to a game's workspace. Shared input and UI become direct choices when the game develops its console flow; import them from `@blacksite/input` and `@blacksite/ui`, then add their packages and dependencies to the workspace. The starter keeps its heads-up display small so the main interaction is visible.

The scaffold initializes Git and two submodules and records its options in `.web-game-stack.json`. Rerun with the same options to repair a partial scaffold; a nonempty unrelated directory or changed options gets a clear refusal. To change systems in an existing game, edit the workspace and package manifest intentionally.
