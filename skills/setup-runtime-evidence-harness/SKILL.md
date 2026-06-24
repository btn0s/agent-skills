---
name: setup-runtime-evidence-harness
description: >
  Create or retrofit an agent instruction harness that enforces one runtime
  evidence path for acceptance. Use when Codex needs to set up AGENTS.md,
  .agents/rules, telemetry or evidence acceptance docs, scenario expectation
  templates, cross-agent instruction links, or project rules that prevent fake
  validation such as smoke tests, dependency checkers, pass/fail scripts,
  sidecar manifests, file-existence claims, or test-run success from replacing
  real runtime evidence. Useful for games, simulations, data pipelines,
  agents, product workflows, browser apps, services, robotics, and any project
  where acceptance must come from observed behavior rather than proxy checks.
---

# Setup Runtime Evidence Harness

## Purpose

Install a project-local agent contract that keeps agents on the real runtime
path. The harness separates four roles:

- **Owners:** systems that produce facts.
- **Drivers:** tests, scripts, users, or tools that exercise the runtime.
- **Evidence:** artifacts emitted by the real runtime path.
- **Acceptance:** a human or agent reading required and contradictory facts
  from the evidence artifact.

The central rule is: drivers may schedule or exercise behavior, but only the
runtime evidence artifact can prove acceptance.

## Workflow

### 1. Inspect The Project

Read existing local guidance first: `AGENTS.md`, `.agents/rules`, `README`,
architecture docs, test docs, CI docs, scripts, and recent plans. Identify:

- The real runtime session: PIE, local server, browser workflow, job run,
  simulator, deployed environment, device session, or production-like replay.
- The single evidence artifact: telemetry JSON, trace, event log, audit record,
  screenshot set, run report generated inside the app, database audit row, or
  another runtime-owned output.
- The scripted driver: functional test, browser automation, CLI job launcher,
  scenario runner, integration test, manual session, or hardware rig.
- The systems that own important facts.
- Existing fake-confidence patterns to forbid.

When adapting an existing project, preserve its terms. Do not rename a healthy
test suite into "telemetry" just to match this skill.

### 2. Choose Harness Terms

Use project-native names for these fields:

| Field | Meaning | Echelon example |
| --- | --- | --- |
| `project_name` | Human project name | `Echelon-GASP` |
| `runtime_session` | The real execution environment | `PIE session` |
| `evidence_artifact` | The only acceptance artifact | `Saved/Telemetry/run_*.json` |
| `driver` | Tool that exercises the runtime | `Unreal Functional Test` |
| `primary_tool` | Preferred editor/runtime tool | `MCP/editor tools` |
| `fallback_tool` | Narrow fallback, if any | `console RPC` |
| `scenario_root` | Scenario expectation doc location | `Content/_Echelon/Tests` |
| `owner_layers` | Ownership boundaries | `GASP`, `Metaxis/UE`, `Echelon` |

### 3. Scaffold The Harness

Prefer the bundled script for a new or mostly missing harness:

```bash
python skills/setup-runtime-evidence-harness/scripts/scaffold_runtime_evidence_harness.py \
  --project-root . \
  --project-name "My Project" \
  --runtime-session "local runtime session" \
  --evidence-artifact "var/evidence/run_*.json" \
  --driver "scripted scenario runner" \
  --primary-tool "native project tools" \
  --scenario-root "scenarios" \
  --owner "Platform owns low-level execution" \
  --owner "Project owns product semantics and evidence emission"
```

The script creates:

- `AGENTS.md`
- `Docs/project-setup.md`
- `Docs/architecture-boundaries.md`
- `Docs/runtime-evidence-acceptance.md`
- `Docs/failed-run-postmortem.md`
- `Docs/adr/0000-template.md`
- `.agents/rules/00-project-contract.md`
- `.agents/rules/01-runtime-evidence-only-acceptance.md`
- `.agents/rules/02-architecture-ownership.md`
- `.agents/rules/03-runtime-workflow.md`
- `.agents/rules/04-failed-run-lessons.md`
- `.agents/rules/05-scenario-evidence-expectations.md`
- `<scenario_root>/README.md`
- `<scenario_root>/SCENARIO_TEMPLATE.md`
- `Scripts/Sync-AgentInstructions.ps1`

By default the script refuses to overwrite existing files. Use `--overwrite`
only after inspecting local guidance and preserving project-specific rules.

### 4. Customize The Generated Contract

After scaffolding, edit the generated docs to remove placeholders and encode the
project's real constraints.

Read [references/file-blueprints.md](references/file-blueprints.md) for the
purpose and expected contents of each generated file.

Read [references/intake-checklist.md](references/intake-checklist.md) when the
project has unclear ownership boundaries, no existing evidence artifact, or a
history of agents inventing validation detours.

### 5. Define Scenario Expectations

For each scenario or slice that requires runtime proof, create a sibling
expectation doc before editing the scenario or test driver. The doc must name:

- Purpose of the scenario.
- Runtime/session command or tool.
- Layout, fixture, data, or environment constraints.
- Required evidence events, fields, screenshots, metrics, traces, or records.
- Contradictory signals in the same artifact.
- Explicit "not acceptance" list.

The scenario driver is never the judge. It only creates the conditions under
which runtime evidence can be emitted.

### 6. Verify The Harness

Before calling the harness installed:

1. Confirm `AGENTS.md` points to the docs and rule files.
2. Confirm the evidence path is singular and concrete.
3. Confirm at least one rule denies each known fake-confidence path.
4. Confirm scenario expectation docs are required before scenario edits.
5. Confirm cross-agent entrypoints point back to the same canonical contract.
6. Run the project-specific sync script if links are desired.

If the project cannot yet emit a runtime evidence artifact, say that the
harness is installed but acceptance is blocked until the runtime owner emits
the artifact.

## Design Rules

- Keep the harness local to the project. Project guidance beats generic skill
  defaults.
- Make forbidden proxies explicit. Agents need named exits blocked.
- Treat missing facts as instrumentation work in the owning system, not as a
  reason to build an external verifier.
- Do not make lifecycle scripts into acceptance scripts.
- Do not let a green driver result, elapsed time, file existence, dependency
  check, or generated summary replace reading the evidence artifact.
- Preserve existing healthy tests. Reclassify what they prove instead of
  deleting them.
- Keep the top-level contract short and delegate details to focused rule files.

## Report Shape

When done, report:

- The files added or updated.
- The chosen evidence path and runtime session.
- The main forbidden proxy checks.
- Any placeholders still requiring project owner input.
- Validation performed, including script validation if applicable.
