# Agent Skills

Personal agent skills published for installation with [skills.sh](https://skills.sh/).

## Install

```bash
npx skills add btn0s/agent-skills --skill autonomous-pm
npx skills add btn0s/agent-skills --skill cursor-debug-mode
npx skills add btn0s/agent-skills --skill setup-runtime-evidence-harness
npx skills add btn0s/agent-skills --skill proof-setup --skill proof-write --skill proof-capture --skill proof-present
```

## Skills

- `autonomous-pm`: Run a project PM loop with subagent reviews, steering, acceptance checks, commits, and one-horizon plans.
- `cursor-debug-mode`: Apply Cursor Debug Mode's hypothesis- and log-driven debugging workflow with a built-in NDJSON log sink.
- `setup-runtime-evidence-harness`: Create AGENTS.md, rules, docs, and scenario templates for runtime-only acceptance.
- `proof-setup`: One installer for the proof skills, plus the shared `proof` tool. macOS on Apple Silicon. After installing, run `~/.agents/skills/proof-setup/install.sh` (`--check` to verify).
- `proof-write`: Write narrated walkthrough scripts that are easy to follow: a spoken agenda, plain English, every line on screen, and terms explained before they're used.
- `proof-capture`: Gather what a proof shows: terminal runs, trace and benchmark data as chart JSON, scripted iOS Simulator recordings (Maestro), and Cap screen recordings.
- `proof-present`: Render and publish: the `proof` tool (terminal beats, charts, timelines, flows, cards, media, Kokoro narration, chapters), tailnet links, and the Cap → Kokoro → Tesseract edit pipeline.
