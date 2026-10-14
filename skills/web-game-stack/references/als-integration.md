# ALS integration

Add `https://github.com/btn0s/als-web.git` as `vendor/als-web` Git submodule and list it in `pnpm-workspace.yaml`. Consume `als-ue5-r3f` source exports. ALS owns the character capsule, locomotion, animation graph, native third-person camera, overlay states, snapshot capture, and remote actor utilities. Its `public` directory supplies the freely redistributable ALS character and animation assets; a game can point Vite `publicDir` there during development.

TPP mounts `Character` and `AlsCamera` in the same Rapier Physics world. The starter imports the ALS footstep audio bridge by source path because that bridge has no public package export yet; promote an export upstream before depending on a second copy. The starter uses native ALS keyboard and pointer input. Register a consumer overlay state for each equipped weapon when the weapon's animation needs more than a stock ALS overlay. FPP mounts the same ALS character and feeds `Character` a semantic `inputSource` from Operator; the third-person pose remains available while a separate arms-only view follows the stable eye.

Use `AlsCharacterRecorder`, `AlsSnapshotBuffer`, and `AlsRemoteActor` for networked characters. Send game state, not a copied skeleton pose each frame. Keep the local and remote character lifetimes tied to their sessions.

Fix shared ALS behavior in its submodule on a game-named branch, publish the ALS commit, then update the game's pointer. A committed pointer must resolve from the remote for a fresh clone. Do not vendor a second ALS source copy into a game or skill. Blacksite's Operator also depends on als-web; the game's top-level ALS workspace package satisfies that source dependency.
