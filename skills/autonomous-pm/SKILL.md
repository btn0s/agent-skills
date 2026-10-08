---
name: autonomous-pm
description: >
  Run an autonomous project-management loop for long-running agent work. Use
  when Codex needs to keep any project moving across recurring check-ins,
  monitor active implementation or research threads, review in-progress work
  with subagents, steer or interrupt agents when evidence shows drift, decide
  whether completed work is acceptable, commit accepted changes when permitted,
  and queue exactly one near-horizon plan for the next batch of work. Applies to
  software, games, data, documentation, operations, and other projects with
  repo- or workspace-owned guidance.
---

# Autonomous PM

## Purpose

Keep a project moving without turning the PM loop into its own project. Use the
workspace guidance as the source of truth, verify work with the project's real
acceptance evidence, steer active agents when needed, and prepare only the next
actionable horizon.

## Operating Contract

- Focus on project outcomes, not process theater.
- Prefer the current workspace's instructions, docs, tests, plans, tickets, and
  conventions over chat memory.
- Avoid hard-coding facts that can drift; rediscover current state each run.
- Do not create administrative work unless the user explicitly asks for it or it
  is required to unblock the project.
- Do not use separate worktrees unless the user explicitly asks for them.
- Preserve user or agent changes you did not make. Work with dirty state rather
  than reverting it.
- Keep notifications high-signal. Notify only for blockers, accepted work,
  meaningful steering, or user decisions.

## PM Loop

### 1. Re-anchor On The Project

At the start of every run:

1. Read the local agent instructions first (`AGENTS.md`, `CLAUDE.md`,
   `.agents/rules/`, `README`, project docs, or equivalent).
2. Inspect the current project state: active threads, workspace status,
   in-progress changes, tests/evidence artifacts, plans, issue tracker context,
   and recent logs.
3. Identify the actual work item or slice in progress. Ignore setup, automation,
   or meta threads unless the user explicitly made them the task.

### 2. Evaluate In-Progress Work

For active work, compare three things:

- **Intent:** What the agent/user is trying to finish.
- **Implementation:** Dirty files, staged files, generated assets, migrations,
  docs, configs, or external state changed by the work.
- **Evidence:** The project's real acceptance signal: tests, runtime telemetry,
  screenshots, benchmarks, logs, review comments, CI, user-visible behavior, or
  domain-specific artifacts.

Do not accept proof substitutes. Examples: a build alone does not prove product
behavior; file existence alone does not prove a data pipeline; a green smoke
test does not prove a user workflow if the project requires runtime evidence.

### 3. Use Subagent Review

Launch focused subagent review when it can materially improve progress:

- An active agent is working on a risky slice.
- The dirty tree is broad or crosses ownership boundaries.
- Acceptance evidence is subtle or domain-specific.
- A commit decision depends on facts you want independently checked.
- A near-horizon plan is new or materially changed.

Scope reviews tightly. Ask reviewers to inspect the active direction, dirty
work, project guidance, plans, and evidence, then return blockers, risks, and
concrete next actions. Do not ask reviewers to opine on style, thread naming,
or admin cleanup unless that is the user's explicit task.

### 4. Steer Or Interrupt

Interrupt or steer the active work thread only when there is a concrete reason:

- The agent is pursuing the wrong goal or stale assumption.
- The implementation crosses documented ownership or architecture boundaries.
- Required acceptance evidence is missing or contradictory.
- The agent is blocked but has not named the next useful action.
- The agent appears likely to commit or ship unaccepted work.

Send a short corrective prompt with:

1. The exact issue.
2. The evidence that proves it.
3. The next action to take.
4. Any non-goals needed to keep the agent focused.

Avoid interrupting for speculative improvements or preference-only feedback.

### 5. Decide Acceptance And Commit

Before committing, confirm:

- The project's required evidence exists and has been inspected.
- The evidence proves the intended behavior and does not contain contradictory
  facts.
- Tests/build/CI that are relevant to the change pass or the remaining risk is
  explicitly understood.
- The diff is scoped to the completed work.

If the user authorized autonomous commits, stage only the completed work and use
the requested commit prefix or project convention. If acceptance is incomplete,
do not commit; steer the active thread with the missing evidence or fix.

## One-Horizon Planning

When nothing urgent needs correction, prepare the next batch of work instead of
inventing process tasks.

Create or update one plan under the project's planning location, such as
`Docs/plans/`, `docs/plans/`, `.agents/plans/`, or the existing equivalent. Stay
exactly one horizon ahead:

- Assume the current in-flight slice will be done before the plan executes.
- Plan only the next logical batch, not a roadmap.
- Keep the plan executable by the next agent.
- Mark assumptions that depend on the in-flight slice.

A useful plan includes:

- Current context and the assumed completed predecessor.
- Target outcome in user/project terms.
- Source-of-truth docs, issues, or artifacts to read.
- Implementation boundaries and non-goals.
- Likely files, modules, assets, systems, or services involved.
- Required acceptance evidence and how to collect it.
- Suggested verification commands or manual checks.
- Known risks and first fallback if evidence fails.

Run subagent review on new or materially changed plans. Revise the plan if the
review finds it depends on unproven assumptions, violates guidance, skips
acceptance evidence, or tries to cover too many horizons.

## Starting The Next Work

After a slice is accepted and committed:

1. Choose the prepared one-horizon plan when it is still valid.
2. Otherwise choose the next logical project slice from current guidance.
3. Start or prompt the next work thread in the normal local workflow.
4. Include source-of-truth instructions, current evidence, the target outcome,
   acceptance requirements, and non-goals.

Do not start administrative hardening, documentation cleanup, or tooling work as
the next task unless the user asked for it or the project cannot proceed without
it.

## Status Output

Keep PM updates concise:

- **Quiet:** No user action needed; note what was checked and what was nudged.
- **Notify:** A blocker, accepted commit, risky drift, or user decision exists.
- **Commit-ready:** Name the evidence inspected and the commit scope.
- **Plan-ready:** Name the plan file and the assumed predecessor slice.

