# State ownership

Koota holds entity identity and continuous gameplay data: transforms, velocity, health, team, inventory, ammunition, deadlines, projectiles, and simulation roots. XState actors hold discrete weapon, life, seat, room, and app phases. Effect holds service dependencies, wire decoding, errors, streams, retries, and resource lifetimes. Colyseus only transports state projections and events.

Run the simulation tick as synchronous code on a simulation clock. Never build or execute Effects inside it. Define Koota queries once with `createQuery`; update AoS trait fields in place and publish with `entity.changed(trait)`. Reuse scratch vectors in tight systems, but copy data when emitting a durable event. A server hosting many rooms should scope entities to a simulation root through Blacksite `sim-core` rather than allocating unbounded independent worlds.

Give each room or session an Effect scope. Acquire timers, telemetry, directory registration, network streams, and actors in that scope and release them together. Decode every named wire message with a shared Effect Schema and derive TypeScript types from it. Use XState for transitions and Koota traits for the data those transitions change; avoid shadow state in React. React subscribes to a revision or queried trait.

Keep pure combat authority in a game-owned protocol package called by both an online room and offline range. Rendering, ALS locomotion, physics presentation, and local input remain client concerns.
