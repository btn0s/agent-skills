# Rendering and physics

Use React Three Fiber for the scene and Rapier for collisions. Mount one Physics world for a local arena and run character motion at a fixed 60 Hz step. Keep visual interpolation and effects outside authority. Read Rapier rigid-body state after physics before publishing snapshots; keep rendering transforms as projections. Use the ALS character's existing capsule rather than adding a second controller body.

A prior Rapier Physics remount could free a live world proxy. If world remounts occur, verify the current `@react-three/rapier` release under strict React replay and scene transitions. If the bug recurs, carry a documented local patch that defers proxy disposal behind a generation check; do not pin a dependency merely because a previous game did. Rupture's patched Rapier is separate and owned by its Blacksite package; the ordinary game scene uses stock Rapier.

Profile actual GPU and physics costs before adding postprocessing. Keep materials and large static geometry shared. Destruction simulation runs in Rupture's worker and publishes compact render effects, rather than causing a full React tree update on every shard.
