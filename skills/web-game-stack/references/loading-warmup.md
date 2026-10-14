# Loading and warmup

Use the bundled `assets/loading/warmup.mjs` registry for game-owned preparation steps. Register named tasks with a stage, scope, and async run function. `runWarmup` reports stage progress, supports abort, and tears down a failed scope cleanly. Recommended order: boot settings and device layer, network session or offline authority, asset downloads, GLB parse and animation sampler compilation, shader/physics warmup, then reveal the player.

A ready flag means the scene has a character, camera, collision world, and input sink; downloading bytes alone is not readiness. Keep a retry action for recoverable asset failures. For multiplayer, room admission and authoritative spawn are separate from client visual readiness. Dispose session resources when changing rooms without freeing resources still used by another mounted scene.
