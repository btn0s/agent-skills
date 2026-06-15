---
name: cursor-debug-mode
description: >
  Apply Cursor's Debug Mode system prompt when investigating reproducible bugs
  with non-obvious root causes. Forces hypothesis-driven debugging with runtime
  evidence, instrumentation logs, and before/after verification before any fix.
  Use when the user is in debug mode, asks to debug a bug, or requests
  systematic root-cause investigation.
---

# Cursor Debug Mode

## Purpose

Switch the assistant into the same systematic debugging posture used by Cursor
Debug Mode. Do not jump to fixes from code inspection alone. Generate
hypotheses, instrument code, collect runtime logs, confirm root causes, fix with
evidence, verify with logs, and only then remove instrumentation.

## Trigger

Apply this skill whenever:

- The user explicitly asks to "debug" an issue or is in a debug/debugging mode.
- A bug is reproducible but the root cause is not obvious from static code.
- You feel tempted to fix from code alone without runtime proof.

## Workflow

### 1. Establish the debugging contract

Open the response by stating the contract in `## Systematic Workflow`:

1. Generate 3–5 precise hypotheses about WHY the bug occurs.
2. Instrument code with logs to test all hypotheses in parallel.
3. Provide clear reproduction steps for the caller.
4. Wait for the caller to confirm reproduction.
5. Analyze logs and label each hypothesis CONFIRMED, REJECTED, or INCONCLUSIVE.
6. Fix only with 100% confidence and log proof.
7. Verify with logs; ask the caller to run again and compare before/after.
8. On confirmed success, remove all debug logs and explain the problem/fix in
   1–2 lines.
9. If verification fails, generate new hypotheses from different subsystems and
   add more instrumentation.

### 2. Instrument with the provided sink

Use `sink/log-debug.js` in this skill (or its language-agnostic pattern) to write NDJSON logs.

- Log path: `./.agent-debug.<pid>.ndjson` (create in the project root).
- Each line must include: `id`, `timestamp`, `location`, `message`, `data`,
  `hypothesisId`.
- Map every log to at least one hypothesis.
- Wrap each injected log in collapsible region markers for the relevant
  language, e.g. `// #region agent-log` / `// #endregion`.

Example sink invocation:

```js
const debugLog = require("./skills/cursor-debug-mode/sink/log-debug.js");
debugLog({
  location: "src/store.js:42",
  message: "cart total before discount",
  data: { cartId, total },
  hypothesisId: "A",
});
```

Python equivalent (inline, when JS is not appropriate):

```python
import json, time, pathlib
log = {
  "id": "log_001",
  "timestamp": int(time.time() * 1000),
  "location": "api/orders.py:88",
  "message": "order total before tax",
  "data": {"order_id": order_id, "total": total},
  "hypothesisId": "B",
}
pathlib.Path(".agent-debug.ndjson").open("a").write(json.dumps(log) + "\n")
```

### 3. Clear old logs before each run

Delete the existing debug log file before the caller reproduces. Prefer the file
removal tool over shell commands (`rm`, `touch`, etc.). Do not create the file
manually; the sink creates it when it first appends.

### 4. Read and analyze logs after reproduction

After the caller confirms reproduction, read the log file. Evaluate each
hypothesis with cited log lines. Do not claim a root cause without pointing to
specific log evidence.

### 5. Keep instrumentation during fixes

Leave all debug logs in place while implementing and verifying the fix. Only
remove them after post-fix verification logs prove success or the caller
explicitly confirms the issue is resolved.

## Critical Constraints

- NEVER fix without runtime evidence first.
- ALWAYS rely on runtime information plus code, never code alone.
- Do NOT remove instrumentation before post-fix verification logs are analyzed
  or explicit success is confirmed.
- Verification requires before/after log comparison with cited entries.
- Do NOT use `setTimeout`, `sleep`, or artificial delays as a fix.
- Do NOT log secrets (tokens, passwords, API keys, PII).
- Prefer precise, minimal fixes that reuse existing architecture.
- If every hypothesis is rejected, generate more hypotheses and add more
  instrumentation.

## Final Message Requirements

Close every debugging iteration with:

- Leading hypotheses for root cause and confidence levels.
- New learnings from logs (which hypotheses were confirmed/rejected/inconclusive).
- Clear, numbered next reproduction steps.
- Or, if resolved, a summary of what was learned and confirmation of the fix.

## On Failure of a Fix

Generate new hypotheses from different subsystems, add fresh instrumentation,
clear old logs, and ask the caller to reproduce again. Iteration is expected.
