#!/usr/bin/env python3
"""Scaffold a runtime-evidence agent harness in a project."""

from __future__ import annotations

import argparse
from pathlib import Path
from textwrap import dedent


def write_file(path: Path, content: str, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        print(f"[skip] {path} exists")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"[write] {path}")


def bullet_lines(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create AGENTS.md, .agents/rules, docs, and scenario templates for runtime-evidence acceptance."
    )
    parser.add_argument("--project-root", default=".", help="Project root to scaffold into.")
    parser.add_argument("--project-name", required=True, help="Human project name.")
    parser.add_argument("--runtime-session", required=True, help="Real runtime session name.")
    parser.add_argument("--evidence-artifact", required=True, help="Only acceptance artifact path or pattern.")
    parser.add_argument("--driver", required=True, help="Scripted/manual driver that exercises the runtime.")
    parser.add_argument("--primary-tool", default="project-native tools", help="Preferred tool for runtime/editor work.")
    parser.add_argument("--fallback-tool", default="", help="Narrow fallback tool, if any.")
    parser.add_argument("--scenario-root", default="scenarios", help="Scenario expectation doc root.")
    parser.add_argument("--owner", action="append", default=[], help="Ownership rule. Repeat for multiple owners.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing generated paths.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.project_root).resolve()
    owners = args.owner or [
        "Platform/runtime systems own low-level execution facts.",
        f"{args.project_name} owns project semantics and evidence emission.",
    ]
    owners_md = bullet_lines(owners)
    fallback = args.fallback_tool or "No fallback tool is approved until documented here."

    files: dict[str, str] = {
        "AGENTS.md": f"""
            # {args.project_name} Agent Contract

            Read these first before making changes:

            1. `Docs/failed-run-postmortem.md`
            2. `Docs/architecture-boundaries.md`
            3. `Docs/runtime-evidence-acceptance.md`
            4. `Docs/project-setup.md`
            5. `.agents/rules/*.md`
            6. `TODO.md`

            ## Non-Negotiables

            {owners_md}
            - `{args.evidence_artifact}` is the only acceptance artifact.
            - `{args.driver}` may drive `{args.runtime_session}`, but it must not decide acceptance.
            - Automation may collect evidence, but must not synthesize proof outside the real runtime path.
            - A green driver result, elapsed time, file existence, dependency check, or generated summary is not acceptance.
            - If a required fact is missing, instrument the real owning system and rerun `{args.runtime_session}`.

            ## Expected Work Shape

            Use real project systems, run `{args.runtime_session}`, collect `{args.evidence_artifact}`, and inspect the evidence timeline or artifact before claiming work is done.

            ## Scenario Work

            For work on a scenario under `{args.scenario_root}`, read or create the matching expectation doc before editing scenario assets, fixtures, data, or driver code. See `.agents/rules/05-scenario-evidence-expectations.md`.

            ## Tooling

            - Primary tool: `{args.primary_tool}`
            - Fallback tool: `{fallback}`

            Lifecycle commands and driver commands are convenience only. They are not acceptance artifacts.

            ## Cross-Agent Sync

            `.agents` is the canonical shared rule directory. Run `Scripts/Sync-AgentInstructions.ps1` after moving or recloning the project to recreate tool-specific entrypoints.
        """,
        ".agents/rules/00-project-contract.md": f"""
            # Project Contract

            ## Source Of Truth

            This repository is the source of truth for `{args.project_name}`. Historical projects, archived scripts, generated reports, and old validation helpers are context only unless explicitly approved by the user.

            ## Design Contract

            - Build real project behavior first.
            - Use `{args.primary_tool}` for normal runtime or asset work.
            - Use `{args.driver}` only to drive `{args.runtime_session}`.
            - Acceptance comes from `{args.evidence_artifact}`.

            ## Clean Restart Rule

            When uncertainty appears, inspect the current project and runtime evidence. Do not invent recovery infrastructure or proxy validation.
        """,
        ".agents/rules/01-runtime-evidence-only-acceptance.md": f"""
            # Runtime-Evidence-Only Acceptance

            `{args.evidence_artifact}` produced by `{args.runtime_session}` is the only acceptance artifact.

            ## Allowed

            - Runtime-owned evidence emitted during a real `{args.runtime_session}`.
            - Rich evidence that includes timestamps, source systems, actor/component/job/request identifiers when available, payloads, and causality.
            - Automation that starts or drives `{args.runtime_session}`, waits for a meaningful buffer, stops or completes it, and collects `{args.evidence_artifact}`.
            - Small utilities that locate, pretty-print, or excerpt evidence without deciding pass/fail.

            ## Forbidden

            - Smoke tests as acceptance.
            - Dependency or class existence checks as acceptance.
            - File existence alone.
            - Sidecar manifests that claim behavior without runtime evidence.
            - Fake summaries generated outside the runtime path.
            - Pass/fail logic outside the owning runtime evidence system.
            - Treating `{args.driver}` success as feature acceptance.

            ## Rule Of Measurement

            If something matters, instrument the real owner and emit it into `{args.evidence_artifact}`.

            ## How Agents Must Judge A Session

            Before claiming acceptance, inspect:

            1. Required facts for the slice.
            2. Contradictory facts in the same artifact.
            3. Movement, routing, state, timing, data, or causality facts that could invalidate partial success.

            Report acceptance in plain language tied to evidence excerpts. Do not report driver success as proof.
        """,
        ".agents/rules/02-architecture-ownership.md": f"""
            # Architecture Ownership

            ## Owner Layers

            {owners_md}

            ## Project Rule

            The project may observe, configure, normalize, and emit project-owned facts. It must not replace upstream owners for convenience.

            ## Data Boundary

            The seam is the owned data boundary, not wrapper count. Add a wrapper only when it owns real semantics or reduces real complexity.
        """,
        ".agents/rules/03-runtime-workflow.md": f"""
            # Runtime Workflow

            ## Normal Loop

            1. Make focused code, asset, data, or configuration changes.
            2. Use `{args.primary_tool}` for normal runtime work.
            3. Run `{args.runtime_session}` using `{args.driver}` or manual project-native workflow.
            4. Collect `{args.evidence_artifact}`.
            5. Inspect the evidence artifact before reporting acceptance.

            ## Tool Precedence

            Prefer `{args.primary_tool}`. Use fallback tooling only when documented and only for operations the primary tool cannot perform.

            ## Lifecycle Scripts

            Lifecycle scripts may open, build, seed, run, or reset the environment. They do not provide acceptance.
        """,
        ".agents/rules/04-failed-run-lessons.md": f"""
            # Failed Run Lessons

            Use this file to preserve lessons from failed or risky implementation runs.

            ## Do Not Build Around Missing Evidence

            Missing evidence means the real owner needs instrumentation. It does not justify a verifier that infers behavior from files.

            ## Do Not Replace Owners

            Respect `Docs/architecture-boundaries.md`. Replacement requires explicit user approval.

            ## Do Not Wrap For Its Own Sake

            Wrappers must own real semantics or simplify real complexity.

            ## Do Not Treat Tooling As Acceptance

            Driver success, elapsed time, logs, setup scripts, generated summaries, and file existence do not replace `{args.evidence_artifact}`.
        """,
        ".agents/rules/05-scenario-evidence-expectations.md": f"""
            # Scenario Evidence Expectations

            Every scenario under `{args.scenario_root}` must have a matching expectation doc.

            ## Gate Rule

            Before changing a scenario, fixture, driver, or slice system:

            1. Read the matching expectation doc.
            2. If missing, write it first.
            3. If requirements change, update the doc before changing implementation.

            ## Required Sections

            - Scenario path/name.
            - Driver name.
            - Purpose.
            - Layout, fixture, data, or environment constraints.
            - How to run.
            - Required evidence from the same session.
            - Failure or contradictory signals.
            - Explicit not-acceptance list.
        """,
        "Docs/runtime-evidence-acceptance.md": f"""
            # Runtime Evidence Acceptance

            ## Principle

            The only acceptance artifact is `{args.evidence_artifact}` produced by the real `{args.runtime_session}`.

            ## Session Shape

            Each meaningful runtime session should produce evidence with:

            - Session or run identifier.
            - Project and scenario name.
            - Start and stop timestamps.
            - Runtime context.
            - Ordered timeline, trace, records, screenshots, or metrics.
            - Payloads rich enough to prove causality.

            ## What Automation May Do

            Automation may start, drive, wait, stop, locate, and excerpt evidence.

            Automation may not assert success from file existence, synthesize events, maintain a separate pass/fail schema, or replace missing runtime facts with logs.

            ## Missing Data Rule

            When a fact is missing, add measurement to the real system that owns the fact. Do not build a new verifier.

            ## Judging A Session

            Read the artifact. Check required facts and contradictory facts from the same session before claiming acceptance.
        """,
        "Docs/architecture-boundaries.md": f"""
            # Architecture Boundaries

            ## Goal

            Make ownership unambiguous so agents do not build unnecessary wrappers, fake harnesses, or replacement systems.

            ## Owners

            {owners_md}

            ## Project Semantics

            `{args.project_name}` owns project-specific semantics and the evidence emitted to `{args.evidence_artifact}`.

            ## Forbidden Pattern

            Do not rebuild an upstream owner before proving it cannot provide the required fact. Do not use a fake sensing, movement, data, UI, or workflow harness as acceptance.
        """,
        "Docs/project-setup.md": f"""
            # Project Setup

            ## Baseline

            - Project: `{args.project_name}`
            - Runtime session: `{args.runtime_session}`
            - Evidence artifact: `{args.evidence_artifact}`
            - Driver: `{args.driver}`
            - Primary tool: `{args.primary_tool}`

            ## Required Setup Artifacts

            - `AGENTS.md`
            - `.agents/rules/*.md`
            - `Docs/architecture-boundaries.md`
            - `Docs/runtime-evidence-acceptance.md`
            - `Docs/failed-run-postmortem.md`
            - `Docs/adr/*.md`
            - `TODO.md`

            ## Runtime Loop

            1. Prepare the project.
            2. Run `{args.runtime_session}`.
            3. Let the runtime emit `{args.evidence_artifact}`.
            4. Inspect the evidence artifact.
            5. Change the real owning system based on missing or wrong facts.

            No separate verifier decides whether the project works.
        """,
        "Docs/failed-run-postmortem.md": f"""
            # Failed Run Postmortem

            ## Known Risks

            Replace this section with real history when available.

            - Agents may mistake driver success for product acceptance.
            - Agents may build dependency verifiers instead of runtime instrumentation.
            - Agents may create generated summaries without reading raw evidence.
            - Agents may replace upstream owners for convenience.

            ## Corrective Rules

            - `{args.evidence_artifact}` is the only acceptance artifact.
            - Automation may drive the runtime, not judge acceptance.
            - Missing facts must be added to the real owning system.
            - Historical artifacts are context, not implementation source.
        """,
        "Docs/adr/0000-template.md": """
            # ADR 0000: Title

            ## Status

            Proposed

            ## Context

            What decision pressure exists?

            ## Decision

            What will the project do?

            ## Consequences

            What becomes easier, harder, or forbidden?
        """,
        f"{args.scenario_root}/README.md": f"""
            # Scenario Evidence Expectations

            Each scenario here is a real project scenario driven by `{args.driver}` or a manual runtime session. Acceptance comes only from `{args.evidence_artifact}` produced by `{args.runtime_session}`.

            ## Gate Rule

            Before editing a scenario, fixture, or driver code, read or create the matching expectation doc.

            Global rules: `Docs/runtime-evidence-acceptance.md` and `.agents/rules/01-runtime-evidence-only-acceptance.md`.
        """,
        f"{args.scenario_root}/SCENARIO_TEMPLATE.md": f"""
            # <Scenario Name> Evidence Expectations

            **Scenario:** `<path or name>`
            **Driver:** `{args.driver}`

            Write or update this file before changing the scenario, fixtures, driver, or slice code it exercises.

            ## Purpose

            State the behavior this scenario proves.

            ## Constraints

            List layout, fixture, data, account, environment, or timing constraints.

            ## How To Run

            1. Start `{args.runtime_session}`.
            2. Drive the scenario with `{args.driver}`.
            3. Inspect `{args.evidence_artifact}` from the same session.

            ## Required Evidence

            | Evidence | Expectation |
            | --- | --- |
            | `<event/field/record>` | `<required payload or observation>` |

            ## Failure Signals

            | Signal | Meaning |
            | --- | --- |
            | `<contradictory fact>` | `<why this rejects acceptance>` |

            ## Not Acceptance

            - Driver success.
            - Elapsed time.
            - File existence alone.
            - Generated summary without raw evidence.
        """,
        "Scripts/Sync-AgentInstructions.ps1": f"""
            param(
                [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
            )

            $ErrorActionPreference = "Stop"

            function Ensure-DirectoryLink {{
                param(
                    [Parameter(Mandatory = $true)][string]$LinkPath,
                    [Parameter(Mandatory = $true)][string]$TargetPath
                )

                if (Test-Path -LiteralPath $LinkPath) {{
                    $item = Get-Item -LiteralPath $LinkPath -Force
                    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {{
                        if ($item.Target -eq $TargetPath) {{ return }}
                        Remove-Item -LiteralPath $LinkPath -Force
                    }} else {{
                        throw "Refusing to replace non-link path: $LinkPath"
                    }}
                }}

                New-Item -ItemType Junction -Path $LinkPath -Target $TargetPath | Out-Null
            }}

            function Ensure-EntrypointFile {{
                param(
                    [Parameter(Mandatory = $true)][string]$LinkPath,
                    [Parameter(Mandatory = $true)][string]$TargetPath
                )

                if (Test-Path -LiteralPath $LinkPath) {{
                    $item = Get-Item -LiteralPath $LinkPath -Force
                    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {{
                        if ($item.Target -eq $TargetPath) {{ return }}
                        Remove-Item -LiteralPath $LinkPath -Force
                    }} else {{
                        return
                    }}
                }}

                Set-Content -LiteralPath $LinkPath -Value @(
                    "# {args.project_name} Agent Contract",
                    "",
                    "Read `AGENTS.md` first. It is the canonical shared instruction file.",
                    "",
                    "The shared rule directory is `.agents/`. Run `Scripts/Sync-AgentInstructions.ps1` to recreate tool-specific links after moving or recloning the project."
                ) -Encoding UTF8
            }}

            $project = (Resolve-Path -LiteralPath $ProjectRoot).Path
            $agentsDir = Join-Path $project ".agents"
            $agentsFile = Join-Path $project "AGENTS.md"

            if (-not (Test-Path -LiteralPath $agentsDir -PathType Container)) {{
                throw "Missing canonical instructions directory: $agentsDir"
            }}

            if (-not (Test-Path -LiteralPath $agentsFile -PathType Leaf)) {{
                throw "Missing canonical instructions file: $agentsFile"
            }}

            Ensure-DirectoryLink -LinkPath (Join-Path $project ".claude") -TargetPath $agentsDir
            Ensure-DirectoryLink -LinkPath (Join-Path $project ".cursor") -TargetPath $agentsDir
            Ensure-EntrypointFile -LinkPath (Join-Path $project "CLAUDE.md") -TargetPath $agentsFile
            Ensure-EntrypointFile -LinkPath (Join-Path $project ".cursorrules") -TargetPath $agentsFile

            Write-Host "Synced agent instructions for {args.project_name}."
        """,
    }

    for relative_path, content in files.items():
        write_file(root / relative_path, dedent(content), args.overwrite)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
