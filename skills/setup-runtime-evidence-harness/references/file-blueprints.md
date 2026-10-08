# Runtime Evidence Harness File Blueprints

Use these blueprints when customizing generated files.

## `AGENTS.md`

Purpose: the front door for agents.

Include:

- Required reading order.
- Non-negotiables.
- Current baseline facts.
- Expected work shape.
- Cross-agent sync note.
- Approved lifecycle commands.
- Tool precedence.

Keep it short. Put detailed doctrine in `.agents/rules` and `Docs`.

## `.agents/rules/00-project-contract.md`

Purpose: source-of-truth and clean-start rules.

Include:

- What is canonical.
- What historical projects or old artifacts may not be copied.
- What counts as project-owned work.
- The preferred change-build-run-evidence loop.

## `.agents/rules/01-runtime-evidence-only-acceptance.md`

Purpose: the strict acceptance doctrine.

Include:

- Allowed evidence artifacts.
- Forbidden proxy checks.
- The measurement rule: instrument the real owner when facts are missing.
- Driver results that are not acceptance.
- How to read the evidence artifact, including contradictory facts.

## `.agents/rules/02-architecture-ownership.md`

Purpose: prevent wrappers, duplicate subsystems, or replacement work.

Include:

- Each owner layer and the facts it owns.
- What the project may observe or configure.
- What the project must not replace.
- The owned data boundary.

## `.agents/rules/03-runtime-workflow.md`

Purpose: define the normal runtime and tooling loop.

Include:

- Normal edit/build/run/evidence loop.
- Scenario authoring rules.
- Tool precedence.
- Fallback tool rules.
- Lifecycle commands and their non-acceptance status.

## `.agents/rules/04-failed-run-lessons.md`

Purpose: encode known mistakes so they do not reappear.

Include:

- Do not build around missing evidence.
- Do not replace upstream owners.
- Do not wrap for its own sake.
- Do not turn restart/rebuild scripts into validation.
- Do not trust polluted historical artifacts without inspection.

## `.agents/rules/05-scenario-evidence-expectations.md`

Purpose: require slice-local expectations before scenario edits.

Include:

- Read or create the matching scenario expectation doc first.
- Required doc sections.
- New scenario creation flow.
- Global acceptance pointer back to `Docs/runtime-evidence-acceptance.md`.

## `Docs/runtime-evidence-acceptance.md`

Purpose: human-readable acceptance doctrine.

Include:

- Principle.
- Session shape.
- Event or artifact shape.
- What automation may and may not do.
- Missing data rule.
- Judging a session.
- Per-scenario expectation policy.

## `Docs/architecture-boundaries.md`

Purpose: stable ownership reference.

Include:

- Upstream/platform owners.
- Integration owners.
- Project semantic owners.
- Forbidden replacements.
- Approved observation/instrumentation seams.

## `Docs/project-setup.md`

Purpose: project-specific operational setup.

Include:

- Baseline.
- Required setup artifacts.
- Runtime loop.
- Tooling and lifecycle commands.
- Scenario authoring rules.

## `Docs/failed-run-postmortem.md`

Purpose: capture cautionary context.

Include:

- What failed.
- Corrective rules.
- Current evidence.
- Agent behavior changes.

If there is no failed run, write a short "Known Risk Register" instead of
inventing history.

## Scenario expectation docs

Purpose: local checklist for one scenario or slice.

Include:

- Scenario asset/path/name.
- Driver name.
- Purpose.
- Environment or layout constraints.
- How to run.
- Required evidence from the same session.
- Failure and contradictory signals.
- Not-acceptance list.
