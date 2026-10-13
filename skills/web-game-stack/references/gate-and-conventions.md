# Gate and conventions

Game gate: `pnpm lint && pnpm typecheck && pnpm build`, exposed as `pnpm check`. The skill's oxlint plugin rejects source comments and test files. Playtest changes in a real browser on a suitable remote device before calling them playable. Do not introduce vitest or a test directory into generated games. Blacksite is a shared engine library and keeps targeted tests for determinism, conservation, structural support, snapshot validation, and public contracts.

Use pnpm workspaces with explicit Blacksite package paths and the ALS submodule. Give game source a narrow `AGENTS.md` explaining the authority split, gate, ignored content locations, and how to promote proven shared improvements back into this skill. If using lefthook, run the same cheap gate before commit. Run react-doctor when changing substantial React UI or hooks, then fix real findings rather than adding blanket suppressions.
