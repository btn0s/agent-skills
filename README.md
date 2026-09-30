# Agent Skills

Personal agent skills published for installation with [skills.sh](https://skills.sh/).

## Install

```bash
npx skills add btn0s/agent-skills --skill autonomous-pm
npx skills add btn0s/agent-skills --skill cursor-debug-mode
npx skills add btn0s/agent-skills --skill setup-runtime-evidence-harness
npx skills add btn0s/agent-skills --skill screen-capture
npx skills add btn0s/agent-skills --skill proof-script
```

## Skills

- `autonomous-pm`: Run a project PM loop with subagent reviews, steering, acceptance checks, commits, and one-horizon plans.
- `cursor-debug-mode`: Apply Cursor Debug Mode's hypothesis- and log-driven debugging workflow with a built-in NDJSON log sink.
- `setup-runtime-evidence-harness`: Create AGENTS.md, rules, docs, and scenario templates for runtime-only acceptance.
- `screen-capture`: Headless PR proof videos (`proof`: terminal beats, animated charts, callouts, Kokoro narration) plus the Cap → Kokoro → Tesseract edit pipeline. macOS on Apple Silicon. After installing, run `~/.agents/skills/screen-capture/install.sh` (`--check` to verify).
- `proof-script`: Write narrated walkthrough scripts that are easy to follow: a spoken agenda, plain English, every line on screen, and terms explained before they're used. Pairs with `screen-capture`.
