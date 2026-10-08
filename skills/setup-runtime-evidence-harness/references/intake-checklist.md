# Runtime Evidence Harness Intake Checklist

Use this when the project is not already clear.

## Required Answers

Ask or infer:

1. What real runtime proves behavior?
2. What artifact is emitted by that runtime?
3. Where is the artifact stored?
4. Who or what emits it?
5. What tool drives the runtime?
6. What does the driver result prove, if anything?
7. Which facts must come from which owning system?
8. What false signals have fooled agents or humans before?
9. What old projects, scripts, generated artifacts, or branches are historical
   context only?
10. What scenario docs must exist before editing scenarios?

## Ownership Prompts

Use these prompts to write boundaries:

- "`<System A>` owns `<low-level behavior>`."
- "`<Project>` may observe `<facts>` and emit `<evidence>`."
- "`<Project>` may not replace `<owner behavior>` unless the user explicitly
  approves that architecture change."
- "The seam is the owned data boundary, not a wrapper count."

## Evidence Prompts

Use these prompts to write acceptance:

- "The only acceptance artifact is `<artifact>` produced by `<runtime>`."
- "`<driver>` is a scripted driver. It is not an acceptance judge."
- "Before claiming acceptance, inspect required facts and contradictory facts in
  the same artifact."
- "If a fact is missing, instrument `<owning system>` and rerun the runtime."

## Common Proxy Checks To Forbid

Forbid every proxy that could be mistaken for acceptance:

- Smoke test success.
- Unit or integration test success when the slice requires runtime evidence.
- Dependency or class existence checks.
- File existence alone.
- Generated summaries without raw evidence.
- Sidecar manifests.
- Logs produced outside the runtime path.
- Screenshots that do not show the required state.
- Elapsed time or "test completed" status.
- Script pass/fail schemas outside the application.

## Installation Validation

The harness is installed when:

- `AGENTS.md` has a clear read order and non-negotiables.
- `.agents/rules` contains focused rule files.
- The acceptance doc names exactly one evidence path.
- Scenario expectation docs are required before scenario edits.
- Existing tests are reclassified as drivers or supporting evidence.
- Cross-agent entrypoints point back to one canonical contract.
