# Promoting a proven change

1. Reproduce the improvement in a playable game or in Blacksite/ALS. Record the behavior, the affected profile, and the gate evidence.
2. If it belongs to a shared package, land it in Blacksite or als-web first. Publish its commit before updating a game's submodule pointer. Keep game-specific content in the game.
3. Update one relevant reference and, if the starter contract changed, the matching bundled asset. Bump `Last verified` in `SKILL.md` only after both scaffold profiles pass the gate and a real browser playtest confirms the interaction. Retire obsolete instructions instead of layering contradictory advice.
4. Run `node scripts/check-skill.mjs`, scaffold catalog, and fresh TPP/FPP directories. Check their packages use caret ranges and their explicit workspace closures match Blacksite manifests. Note any unverified visual or deployment behavior in the report.
