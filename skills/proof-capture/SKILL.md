---
name: proof-capture
description: >-
  Gather the raw material for a proof or walkthrough video: terminal runs, trace and benchmark data turned into
  chart JSON, scripted iOS Simulator recordings (Maestro), and screen or window recordings (Cap). Use when the
  user asks to record, capture, or screenshot something for a PR, a demo or a walkthrough. The script comes from
  proof-write, and the render and publish happen in proof-present.
---

# Capturing material for a proof

Capture only what the script needs. Every beat in `proof.yaml` points at something real: a command that runs, a JSON file taken from the source, or a recording. Nothing is mocked up to look like evidence.

Setup lives in proof-setup. Run `~/.agents/skills/proof-setup/install.sh --check` first, add `--screen` for Cap and `--maestro` for Simulator flows.

Pick the lightest source that proves the point:

| The proof is… | Capture it as | Beat |
| --- | --- | --- |
| Terminal output | Nothing to capture: `proof` runs the command live in a pty | `run:` |
| Numbers (perf, sizes, counts) | JSON pulled from the source | `chart:` / `timeline:` |
| A still UI state | A screenshot | `image:` |
| A mobile flow | A Maestro recording | `video:` |
| A desktop app flow | A Cap recording | `video:` |

Keep each capture in its own folder next to its spec, e.g. `~/dev/captures/<slug>/` with `proof.yaml`, data files and `recordings/`.

## Terminal

Terminal beats are the recording. Put the repo in the state you're demonstrating (`setup:` runs invisibly first), keep the output short (pipe through `grep`/`tail`), and let callouts find text on screen. See proof-present for the beat keys.

## Data: traces and benchmarks

Pull numbers from the system of record, never from a chart image in a PR.

- **Charts:** `{"x": [...], "series": {name: [...]}, "unit": "ms"}`. A bench script can write it during a visible `run:` beat, and the chart beat reads `file:`.
- **Timelines (stage waterfalls):** `{"runs": {"Before (#123)": {"total": 42.749, "stages": [[name, start, dur], ...]}}}`, with seconds from the start of the measured span. Keep three decimals and let the renderer round.
- **Traces** (Cloud Trace, Jaeger, Honeycomb and similar): fetch the trace by ID and pick the spans that bracket what you timed. Convert them to `[name, start - t0, dur]` and record the trace IDs, host and date for the chart's `source:` line. APIs rate-limit (HTTP 429), so retry with backoff.
- Know what each span covers before you name it on screen. Some spans measure the time since the previous stage rather than the stage's own work, so read the code or docs. Put plain-language names in the spec's `labels:` rather than editing the data.
- Save the raw responses next to the JSON (`before.json`, `after.json`) so every number on screen can be re-checked.

## iOS Simulator with Maestro

Write a Maestro flow with `startRecording: <name>` / `stopRecording` around each step. Run it with `maestro test flow.yaml` and `MAESTRO_CLI_NO_ANALYTICS=1 MAESTRO_CLI_ANALYSIS_NOTIFICATION_DISABLED=true`, then point one `video:` beat at each recording. Never use `maestro record` without `--local`, because the default mode uploads the screen to mobile.dev.

Drive the app deterministically, not by tapping around. Add a debug-only, simulator-only deep link that injects input events, for example `myapp://debug-input?keys=right,right,a&interval=400` feeding the app's controller-event stream, and call it with `openLink`. This exercises the real focus and controller paths, and every run is identical.

Maestro on iOS, checked against its docs and issue tracker:

- The first deep link on a fresh simulator shows iOS's "Open in …?" alert. Accepting it is permanent for that simulator, so handle it once in the flow with a conditional `runFlow: {when: {visible: "Open in .*"}, …}`.
- In landscape, Maestro's element hierarchy and its tap-by-text are rotated 90° ([#3595](https://github.com/mobile-dev-inc/Maestro/issues/3595)), and tapping by text can hit the view underneath an alert. Do the text navigation first, or tap with percentage `point:`s taken from a landscape screenshot.
- `setOrientation` persists across `launchApp` and across runs, so set it at the top of the flow.
- Recordings are always in panel orientation, so a landscape run comes out sideways. Set `rotate: ccw` for `LANDSCAPE_LEFT` or `rotate: cw` for `LANDSCAPE_RIGHT` in `proof.config.yaml`, and check one frame.

## Screen and window recording with Cap

```sh
export PATH="$HOME/.local/bin:$HOME/.cap/bin:$PATH"
cap doctor --json          # need permissions.screenRecording == "granted" and captureReady
cap targets --json                               # pick a screen id or window id
cap record start --window <id> --fps 60 --path raw/take1.cap --detach --json
#   ... perform the actions (or have the user perform them) ...
cap record stop --path raw/take1.cap --json
cap project validate raw/take1.cap
cap export raw/take1.cap -o raw/take1.mp4 --quality maximum --json
```

For quick captures, `proof shot [--window "App"] --slug x` takes a still and `proof clip --duration 8 [-- cmd]` records a clip.

- **Screen Recording permission** belongs to the *responsible process*. Over SSH or Tailscale SSH, that's the SSH daemon, which a person grants once, so `cap record` works headless. Apps launched on screen (Terminal and so on) do **not** inherit the grant, so `cap doctor` run *inside* a recorded Terminal reports "not granted". Never try to bypass TCC.
- Prefer `--window` over `--screen`. It keeps the frame tight and hides notifications.
- Use `--duration N` for unattended, fixed-length takes. Add `--mic "<name>"` only when the user wants live voice rather than TTS, and `--system-audio` only if app sounds matter.
- Studio mode (the default) keeps editable cursor and zoom data. Before exporting, adjust it with `cap project config set` (`cursor.hide`, shadow 0 for terminal footage).
- Stills: `cap screenshot --window <id> --path stills/step1.png --json`.
- **Drive a terminal on screen without Apple Events.** Generate a `.terminal` profile whose `CommandString` runs a self-typing script, then launch it with `open demo.terminal` over SSH. Size the window with `printf '\e[3;0;25t\e[8;38;140t'`. Have the script wait for a `go` file so recording starts first, and log `mark <name>` timestamps so you can find beats later. Prefer `run:` beats in `proof` unless the terminal app itself is part of the proof.

## Before handing off to proof-present

- Every file the spec references exists, and one frame of each recording looks right (orientation, nothing private on screen).
- Every number in the JSON can be traced to a saved raw response.
- Recordings hold only the action. Leave the narration to the script.
