# Agent Skills

Personal agent skills published for installation with [skills.sh](https://skills.sh/).

## Install

```bash
npx skills add btn0s/agent-skills --skill autonomous-pm
npx skills add btn0s/agent-skills --skill cursor-debug-mode
npx skills add btn0s/agent-skills --skill local-image-generation
npx skills add btn0s/agent-skills --skill owned-assets
npx skills add btn0s/agent-skills --skill web-game-stack
npx skills add btn0s/agent-skills --skill setup-runtime-evidence-harness
npx skills add btn0s/agent-skills --skill proof-setup --skill proof-write --skill proof-capture --skill proof-present
```

## Skills

| Skill | Purpose |
| --- | --- |
| `autonomous-pm` | Run a project PM loop with subagent reviews, steering, acceptance checks, commits, and one-horizon plans. |
| `cursor-debug-mode` | Apply Cursor Debug Mode's hypothesis- and log-driven debugging workflow with a built-in NDJSON log sink. |
| `local-image-generation` | Route image generation, editing, and inspection requests to the local `imgen` CLI. |
| `owned-assets` | Route asset sourcing to the local `assets` CLI, which searches every pack the user owns on itch.io and Fab. |
| `web-game-stack` | Scaffold TPP, FPP, or blank ALS and Blacksite web games with explicit systems, guidance, and gates. |
| `setup-runtime-evidence-harness` | Create AGENTS.md, rules, docs, and scenario templates for runtime-only acceptance. |
| `proof-setup` | Install the proof skills and shared `proof` tool on macOS Apple Silicon; run `~/.agents/skills/proof-setup/install.sh` (`--check` to verify). |
| `proof-write` | Write narrated walkthrough scripts with a spoken agenda and terms explained before use. |
| `proof-capture` | Gather terminal runs, chart data, scripted iOS Simulator recordings, and screen recordings. |
| `proof-present` | Render and publish narrated videos, attachments, and tailnet links. |
