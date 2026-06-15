# Canonical Guided Reference Examples

Use these examples as the output standard. They are not copy to paste verbatim;
they show the level of specificity, section shape, and evidence expected from
the walkthrough skill.

## Example 1: Broad Codebase Guided Reference

Use this shape when the user asks for a walkthrough of a whole repository,
large subsystem, platform branch, or multi-lane architecture.

### Page Title

`Project Name Guided Reference`

### Premise

This guide explains the project from first principles: what the system is for,
how its major parts fit together, where the important files live, what contracts
cross subsystem boundaries, and which commands prove each lane is healthy. Read
it once from top to bottom, then use the section titles as a debugging map.

### Sections

| Section | Required subsections | Visual |
|---------|----------------------|--------|
| 00 System Overview | Purpose, Main loop, Why the branch is strict, Basic vocabulary, Useful first question | Mermaid flowchart of the end-to-end loop |
| 01 Repository Scope and Ownership | Purpose, Active scope, Excluded scope, Ownership lanes, First files to read | Mermaid lane map |
| 02 Packaging Reference | Purpose, Main files and responsibilities, Data flow, Required contract, Commands, Example workflow, Debugging questions | Mermaid pipeline from manifest to package |
| 03 Runtime Reference | Purpose, Important terms, Capture path, Encode path, Health contract, Healthy checklist, Fields worth learning | Mermaid runtime pipeline |
| 04 Validation Reference | Purpose, What the harness measures, Score components, Evidence levels, Commands, How to read a result | Mermaid evidence ladder |
| 05 Telemetry Reference | Purpose, Normalized session model, Producer contracts, UI/API boundary, Commands, Triage map | Mermaid ingest/normalize/query flow |
| 06 Protocol and Client Reference | Purpose, Wire contract, Shared client core, Input semantics, Client surfaces, Codec gates, Commands | Mermaid protocol/client graph |
| 07 Infrastructure and Serving Reference | Purpose, Target types, Serving model, Capacity planning, Cloud safety, Commands | Mermaid target resolution map |
| 08 Debugging and Proof Workflow | Purpose, Step-by-step workflow, Questions by lane, First-green commands, Cross-lane rule | Typographic callout or Mermaid proof loop |

### Section Body Example

```html
<h2>Runtime Reference</h2>

<h3>Purpose</h3>
<p>
  The runtime is the live bridge between a launched workload and connected
  clients. It owns capture, encode, audio, health reporting, and transport
  handoff. A packaging problem describes what should launch; a runtime problem
  describes what happens after launch begins.
</p>

<h3>Main files and responsibilities</h3>
<table class="reference-table">
  <tr><th>Capture</th><td><code>crates/capture/src/</code> owns frame acquisition and handoff.</td></tr>
  <tr><th>Encode</th><td><code>crates/encode/src/</code> owns hardware encode and codec-facing counters.</td></tr>
  <tr><th>Server</th><td><code>crates/server/src/</code> joins media, transport, input, and health.</td></tr>
</table>

<h3>Healthy runtime checklist</h3>
<ul>
  <li>The workload process leaves startup state after its startup delay.</li>
  <li>The encoder reports the promoted codec path, not a stub fallback.</li>
  <li>Audio has a live source before browser playback is blamed.</li>
</ul>

<h3>Commands</h3>
<div class="command-list">
  <code>cargo test -p stream-capture -p stream-encode -p stream-server</code>
  <code>just dev-status</code>
</div>

<h3>Debugging questions</h3>
<ul>
  <li>Is the process actually running, or only declared launched?</li>
  <li>Did the failure happen before capture, during encode, or after transport?</li>
  <li>Which health field should have changed but did not?</li>
</ul>
```

## Example 2: Focused Subsystem Guided Reference

Use this shape when the user asks for one feature, crate, package, service, or
workflow instead of the entire repository.

### Page Title

`Telemetry Service Guided Reference`

### Sections

| Section | Required subsections | Visual |
|---------|----------------------|--------|
| 00 What This Service Does | Purpose, Inputs and outputs, Core vocabulary, Healthy behavior | Mermaid input/output graph |
| 01 Data Model Reference | Main entities, Required fields, Derived fields, Versioning rules, Example record | Entity relationship or flowchart |
| 02 Producer Contract | Who writes events, Envelope shape, Rejection rules, Backward compatibility, Debugging questions | Mermaid producer-to-ingest flow |
| 03 API Reference | Main routes, Auth boundary, Query patterns, Error behavior, Commands | Route map |
| 04 UI Reference | Main screens, State ownership, Evidence preview, Empty/error states, Files to read | UI state map |
| 05 Operations Reference | Storage layout, Retention, Reporting, Smoke checks, Common failures | Operational lifecycle |
| 06 Debugging Workflow | Triage order, First commands, What to inspect, Stop conditions | Proof loop |

### Good Tables

```html
<h3>Producer contract</h3>
<table class="reference-table">
  <tr><th>Required id</th><td><code>session_id</code> joins server, client, and artifact evidence.</td></tr>
  <tr><th>Timestamp</th><td>Use producer time for raw evidence and normalized time for UI ordering.</td></tr>
  <tr><th>Rejection</th><td>Reject envelopes that cannot be tied to a known schema version.</td></tr>
</table>
```

### Good Debugging Questions

- Can the raw artifact be found before normalization starts?
- Did ingest reject the envelope, or did normalization drop a field?
- Is the UI missing data, or is the API response already incomplete?
- Which schema version does the producer think it is writing?

## Example 3: Non-Code Process Guided Reference

Use this shape for policy, operations, planning, or product workflows where the
source material is docs, meeting notes, screenshots, or user-provided context.

### Page Title

`Release Readiness Guided Reference`

### Sections

| Section | Required subsections | Visual |
|---------|----------------------|--------|
| 00 Workflow Overview | Purpose, Participants, Inputs, Outputs, Vocabulary | Mermaid process overview |
| 01 Entry Criteria | Required artifacts, Ownership, Timing, Rejection conditions | Checklist flow |
| 02 Review Path | Step-by-step workflow, Decision points, Evidence to preserve, Escalation | Sequence diagram |
| 03 Quality Gates | Gate table, Commands or checks, Pass/fail meaning, Common false positives | Gate ladder |
| 04 Reporting | Status format, Audience, Source of truth, Update cadence | Reporting flow |
| 05 Failure Handling | Common failures, Who decides, Rollback path, Communication checklist | Incident branch diagram |
| 06 Operator Checklist | First action, Verification, Done criteria, Follow-up | Typographic callout |

### Good Command Or Check List

```html
<h3>Quality gates</h3>
<div class="command-list">
  <code>Run the release readiness checklist from docs/releases/readiness.md</code>
  <code>Confirm all blocking issues have an owner and due date</code>
  <code>Archive final evidence in the release folder</code>
</div>
```

For non-code topics, a "command" can be a concrete operational check. It still
needs to be specific enough that two readers would do the same thing.

## Anti-Examples

Do not produce section sets like this:

| Weak title | Why it fails |
|------------|--------------|
| The Big Picture | Too vague unless paired with concrete subsections and vocabulary. Prefer "System Overview". |
| Into the Pipeline | Clever but not useful as a reference title. Prefer "Runtime Pipeline Reference". |
| Trust the Flow | Sounds polished but does not tell the reader what they will learn. Prefer "Validation and Evidence Workflow". |
| The Final Mile | Ambiguous. Prefer "Debugging and Proof Workflow". |

Do not produce section bodies like this:

```html
<h2>Runtime Magic</h2>
<p>The runtime is where everything comes alive. Frames move through the system
and clients receive a smooth experience.</p>
<p>This area is important because performance and reliability matter.</p>
```

It has no files, commands, contracts, vocabulary, or debugging handle.

## Canonical Quality Checklist

Before finishing, the generated guide should contain:

- At least one "System Overview" or equivalent first-principles section.
- Straightforward section titles that work as a table of contents.
- Multiple `<h3>` subsections in every major section.
- At least one table mapping files, contracts, fields, gates, or ownership.
- Commands or concrete checks wherever the topic has validation steps.
- Source paths, document names, or links when explaining existing material.
- Debugging questions that help a reader decide where to look first.
- One structural visual per major section, with a caption.
- A final workflow/checklist section that turns the reference into action.
