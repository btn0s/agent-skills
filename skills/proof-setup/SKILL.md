---
name: proof-setup
description: >-
  Install and check everything the proof skills need (proof-write, proof-capture, proof-present): the `proof`
  tool, Kokoro narration, tailnet publishing, GitHub attachments, Cap, Maestro. Use on a new machine, after
  `skills update`, or when a proof command fails because something is missing.
---

# Setting up the proof skills

This skill holds the shared pieces the other proof skills use: the `proof` tool, its scripts, and one installer for all of them.

Get the whole set:

```sh
npx skills add btn0s/agent-skills --skill proof-setup --skill proof-write --skill proof-capture --skill proof-present -g -y
```

## Install

```sh
~/.agents/skills/proof-setup/install.sh          # core + narration
~/.agents/skills/proof-setup/install.sh --check  # what's there and what's missing; changes nothing
```

Run `--check` first in a new environment. If core is missing, it exits non-zero; run the installer before recording anything. The script is idempotent.

| Needs | For | Installed by |
| --- | --- | --- |
| macOS on Apple Silicon, SF Mono (ships with Terminal.app) | everything | the OS |
| `uv`, `~/.local/bin/proof`, the script's Python deps (ffmpeg is bundled) | `proof run` | `install.sh` |
| mlx-audio 0.5.7 with `misaki[en]` on Python 3.12, plus the Kokoro and spaCy models (~350 MB) | narration, on by default | `install.sh` (skip with `--no-narrate`) |
| Tailscale signed in, `dev.captures.serve` LaunchAgent, `tailscale serve /captures` | publishing links | `install.sh --publish`; Tailscale itself is installed and signed in by a person |
| Cap.app and `~/.cap/bin/cap`, Screen Recording permission | `proof shot`, `proof clip`, the Cap pipeline | `install.sh --screen`; the permission is granted by a person in System Settings |
| Maestro and JDK 21 | scripted iOS Simulator captures | `install.sh --maestro` |
| `tsrct`, pinned version | full Tesseract edits | the tesseract-video skill's `references/installation.md` |

The installer never uses `tailscale funnel`, never grants TCC permissions, and never changes network settings. Without `--publish`, render with `proof run --no-publish`.

The installer also reports whether proof-write, proof-capture and proof-present are installed next to it.
