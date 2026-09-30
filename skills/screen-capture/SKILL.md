---
name: screen-capture
description: >-
  Record, annotate, and narrate a screen capture end to end. Use when the user asks for a screen recording,
  demo video, walkthrough, tutorial, or narrated capture, or runs /screen-capture. Records with the Cap CLI,
  narrates with local Kokoro TTS (mlx-audio), and annotates and assembles with Tesseract (tsrct).
  For PR proofs and CLI/terminal demos, use the one-command `proof` tool first (see "Fast path").
---

# Screen capture: record → annotate → narrate

## Fast path: `proof` (use this first)

For PR proofs, choose the lowest tier that proves the change. One spec file becomes one command,
which gives you a published tailnet link. There's no screen recording, TCC or GUI involved:
terminal beats run in a real bash under a pty and are rendered frame by frame.

| Tier | When | Command | Typical time |
| --- | --- | --- | --- |
| 0 still | Proving a visual state exists | `proof shot [--window "App"] --slug x` | <1s |
| 1 raw | Terminal output is the proof, no polish | `proof run spec.yaml --raw` | ~10s |
| 2 captioned | The default for PRs: captions and callouts | `proof run spec.yaml` | ~13s |
| 3 narrated | Reviewers or stakeholders who won't read captions | `proof run spec.yaml --narrate` | ~19s |
| GUI clip | The proof is in a GUI app | `proof clip --duration 8 [-- cmd]` (Cap) | real time |
| Full edit | Marketing-grade demos | The Cap → Kokoro → Tesseract pipeline below | minutes |

Minimal spec. Callouts are found **by text** in the terminal, so there are no coordinates to maintain:

```yaml
title: "Fix: slugify keeps accented letters"
subtitle: "fix/slugify-accents → main"   # both shown only if title_card: true
cwd: ~/dev/proof-demo
setup: [git config color.ui always]        # runs invisibly before recording
beats:
  - run: python3 -m unittest 2>&1 | grep -E '^(AssertionError|FAILED)'
    caption: "On main, the two accent tests fail."
    say: "On main, the two tests with accented titles fail."   # used only with --narrate
    callout: {find: "FAILED (failures=2)", label: "Bug reproduced on main"}
  - clear: true
    run: python3 -m unittest -q
    callout: [{find: "OK", label: "4 / 4 tests pass"}]
```

Beat keys:
- `run` (type it and execute) or `type` (type only).
- `clear`, `caption`, `say`, `hold`, `timeout`.
- `callout`: `{find, label, nth}` or a list of those.

Chart beats show data without screen capture, and can be mixed with terminal beats. Data comes from real output: `file:` reads JSON that an earlier beat wrote, and `cmd:` runs a command that prints JSON. The format is `{"x": [...], "series": {name: [...]}, "unit": "ms"}`.

```yaml
  - run: python3 bench.py main perf/x        # visible; also writes bench.json
  - chart: {file: bench.json, kind: line, title: "runtime vs. size", x_label: "items",
            marks: [{series: perf/x, x: 16000, label: "{ratio:.0f}× faster"}]}   # or kind: bar
    caption: "main grows quadratically; the fix stays flat."
```

Media beats put screenshots and recordings (Simulator, device, game capture) in the same video. A portrait clip sits on the right, with the heading and caption in a left column; landscape media fills the frame above the caption:

```yaml
  - video: recordings/02-start.mp4     # or image: shots/after.png
    heading: "Start a session"          # optional; the PR step's bold heading
    caption: "The mock control plane walks provisioning to ready."
    trim: [0.5, 6]                      # optional, seconds
    speed: 1.5                          # optional
```

Scripted Simulator captures: write a Maestro flow with `startRecording: <name>` / `stopRecording` around each step, run it with `maestro test flow.yaml` (set `MAESTRO_CLI_NO_ANALYTICS=1`), and point one `video:` beat at each recording. Never use `maestro record` without `--local`, because the default mode uploads the screen to mobile.dev.

`{ratio}` means the first series divided by the marked one at that x, so labels track the real numbers.
Terminal callouts accept `regex: true` for dynamic text, for example `find: "\\d+x(?= *$)"`.
Chart titles get the unit appended, e.g. "runtime vs. size (ms)". The line under the title is `source:`, which defaults to "Measured on <host>, <date>"; set it to the real conditions, for example `source: "M4 Pro · Python 3.13 · best of 3"`.
There is a full example in `proof/examples/perf.yaml`, and `mkperf.sh` rebuilds its demo repo.

Default look (keep it this way unless the user asks). It follows the btn0s/desktop and katana proof charts plus the dataviz tokens:
- Flat page `#111110`: no window chrome, traffic lights, step counters, eyebrows or outro card. The title card is opt-in (`title_card: true`), because the PR heading already carries the title.
- The terminal text sits on the page with a 120px margin. The prompt is just the muted cwd.
- A callout underlines the match in accent blue `#3987e5`, dims every other row, and puts the label as plain text beside it. No pills, boxes or amber.
- The caption is one plain line, bottom-left, in secondary ink.
- Charts:
  - Before/after uses a gray baseline and one blue accent.
  - Solid hairline grid, legend top-left.
  - Values are labelled only at the line ends, in ink, never in the series colour.
  - Marks are plain text next to the value.
- Keep captions to facts, with no taglines or outro slogans.

Spec keys:
- `title_card: true` shows a quiet left-aligned title/subtitle for 1.8s first.
- `size: [cols, rows]`. The terminal auto-crops to what was used; `fit: false` disables this.
- `prompt: [user, cwdlabel]`, `env`, `max_gap` (idle output longer than this is compressed), `voice`, `speed`.

Flags:
- `--no-publish`
- `--slug`
- `--out`
- `--pr N --repo owner/name` writes `pr-comment.md`, which contains only the video link.
- `--post` comments via `gh`, but only on PRs authored by btn0s, and only after the user confirms.

The JSON output contains:
- `url`: the direct `proof.mp4` link. Only the video is published: no HTML page, and no text outside the video.
- `mp4`
- `contact_sheet`
- `callouts_not_found`
- per-beat placement
- timings

**Always open `contact_sheet` before sharing.** If `callouts_not_found` is not empty, fix the `find` text.

Tips:
- Keep output short so the terminal crops small and the text renders large. Pipe noisy commands through `grep` or `tail`.
- Put `git switch` and other state setup in `setup:` or at the start of a beat. The recording is real, so the repo must actually be in the demonstrated state.
- Example specs are in `proof/examples/` (copy them to `~/dev/proof-specs/`); `mkdemo.sh` rebuilds the demo repo.
- The tool is at `proof/proof.py` (PEP 723 uv script) and runs through the `proof` wrapper. Install it once with
  `ln -sf <this skill dir>/proof/bin/proof ~/.local/bin/proof` (it needs `uv` on PATH).


Three local tools, one pipeline:

| Stage | Tool | Skill with the details |
| --- | --- | --- |
| Record | `cap` (Cap Desktop CLI) | `cap` (routing + `cap guide --json`) |
| Narrate | Kokoro-82M via `mlx_audio.tts.generate` | this skill, `scripts/narrate.py` |
| Annotate + edit + export | `tsrct` (Tesseract) | `tesseract-video`, `tesseract-motion` |

Read the linked skills before running their commands. This file is the order of operations, not a
replacement for them.

## 0. Preflight

```sh
export PATH="$HOME/.local/bin:$HOME/.cap/bin:$PATH"
cap doctor --json          # need permissions.screenRecording == "granted" and captureReady
mlx_audio.tts.generate --help >/dev/null && echo tts-ok
TSRCT="$HOME/Library/Application Support/Tesseract/bin/tsrct"; "$TSRCT" --version
```

- **Screen Recording permission** belongs to the *responsible process*. Over SSH or Tailscale SSH, that's
  the SSH daemon (`/usr/local/bin/tailscaled` on the devbox), which has been granted, so `cap record`
  works headless. Apps launched on screen (Terminal and so on) do **not** inherit the grant, so `cap doctor`
  run *inside* a recorded Terminal reports "not granted". To show the recorder on camera, use
  `cap record status`, not `cap doctor`. Never try to bypass TCC.
- If `tsrct` is missing or its version doesn't match `tesseract-video/references/cli-version.txt`, follow
  `tesseract-video/references/installation.md`. Don't substitute another version.
- The first Kokoro run downloads about 350 MB (the model plus a spaCy English model) into `~/.cache/huggingface`.

Keep each capture in its own folder, for example `~/dev/captures/<slug>/`, containing `raw/`, `audio/`,
`stills/` and `out/`.

## 1. Plan (before recording)

Write `script.txt`, one narration beat per line. A beat is one action on screen plus the sentence spoken
over it. Optionally prefix a beat with the timestamp where it should start (`mm:ss.s |`). Without
timestamps, beats run back to back.

```
00:00.0 | This is the new settings panel.
00:04.5 | Click Integrations, then choose GitHub.
          Authorize, and the repo list fills in automatically.
```

Keep beats short (at most about 12 words, 3–5 s each). Do an action, then narrate it. Never script claims the
recording doesn't show. Don't invent speech or captions: all narration comes from this script, which the user
approves.

## 2. Record with Cap

```sh
cap targets --json                               # pick a screen id or window id
cap record start --window <id> --fps 60 --path raw/take1.cap --detach --json
#   ... perform the actions (or have the user perform them) ...
cap record stop --path raw/take1.cap --json
cap project validate raw/take1.cap
cap export raw/take1.cap -o raw/take1.mp4 --quality maximum --json
```

- Prefer `--window` over `--screen`. It keeps the frame tight and hides notifications.
- Use `--duration N` for unattended, fixed-length takes. Add `--mic "<name>"` only when the user wants live
  voice rather than TTS, and `--system-audio` only if app sounds matter.
- Studio mode (the default) keeps editable cursor and zoom data. Adjust it with
  `cap project config get|set raw/take1.cap` before exporting. Instant mode is for quick shareable links.
- Stills for thumbnails and annotation references: `cap screenshot --window <id> --path stills/step1.png --json`.
- For a fully automated, cinematic web-page demo (virtual input, 3D camera), the `cap-demo` skill may fit
  better.

## 3. Narrate with Kokoro

```sh
python3 ~/.claude/skills/screen-capture/scripts/narrate.py script.txt audio/ \
  --voice af_heart --speed 1.0
```

This writes `audio/beat-01.wav` … (24 kHz mono) and `audio/manifest.json`, which lists each beat's text,
requested `start`, and measured `duration` in seconds. Use those durations to place clips and to check
each beat fits before the next action. If a beat runs long, shorten the line or bump `--speed`
(1.05–1.15 still sounds natural) rather than speeding up the video.

Voices: `af_heart` (default, warm), `af_bella`, `af_nicole`, `am_michael`, `am_fenrir`, `bf_emma` and
`bm_george` (British, `--lang b`). One-off line:
`mlx_audio.tts.generate --model mlx-community/Kokoro-82M-bf16 --voice af_heart --lang_code a --text "…"
--output_path audio --file_prefix line --join_audio`.

## 4. Annotate, assemble, export with Tesseract

Follow `tesseract-video` (editing, audio, timing, delivery) and `tesseract-motion` (callouts, highlights,
lower thirds, and zoom and pan). In outline:

1. `tsrct project create` a project for the capture, and import `raw/take1.mp4`.
2. Import each narration clip with `tsrct project import-asset --kind audio`, and place each one at its
   manifest `start` (or at the matching on-screen action). Leave 0.2–0.4 s of breathing room between beats.
3. Annotate. Use the motion skill's primitives for arrows, boxes, spotlights, step labels and zooms on the
   action each beat describes. Time each annotation to its beat and keep it on screen for the beat's
   duration. Use at most one focal annotation at a time.
4. Trim dead air, such as waiting for loads or cursor wandering, using the video skill's editorial guidance.
   Keep the narration in sync after cuts.
5. Review with the filmstrip and waveform checks described in `tesseract-video`, then export an MP4 to
   `out/`.

### Lessons from headless terminal demos

- **Drive the screen without Apple Events.** Generate a `.terminal` profile whose `CommandString` runs a
  self-typing script, then launch it with `open demo.terminal` over SSH. Size and place the window with
  `printf '\e[3;0;25t\e[8;38;140t'`. Have the script wait for a `go` file so recording starts first. Run
  `clear` before the first prompt, and have the script log `mark <name>` timestamps so you can find beats in
  the footage.
- **Hide the cursor, remove the shadow.** Before `cap export`, use `cap project config set` with `cursor.hide`
  and a shadow of 0.
- **Frame by scaling, then matte.** Scale each footage segment 110–150% about the terminal's top-left corner
  (anchor at the source content origin), then cover the title bar and window edge with background-colored
  rects that sit above the media. Pick the scale per segment by line length.
- **Jump-cut long waits** (for example TTS synthesis) and label them ("15 s skipped"). Use still frames
  (`ffmpeg -ss T -frames:v 1`, imported with `--kind image`) to hold on completed output after the terminal
  clears.
- **Fonts:** `tsrct project import-font` for each weight, then reference the *typographic* family and style
  (`"Inter"/"SemiBold"`), not the legacy `"Inter SemiBold"/"Regular"` name. Otherwise export fails with
  `missing_fonts`.
- **Callout labels** go in an empty row next to the highlight (36 px tall, 24 px text), never over other
  output. For long wrapped lines, put an inline tag at the end of the row.
- **Build the edit from a script.** Commit the media layers (video, image and audio segments) through
  `checkout`/`commit`, keep a copy of that `.tsrct`, and then `apply` one generated action batch of rects,
  text, groups and opacity keyframes. To iterate, restore the copy and re-apply. `scripts/build_edit_example.py`
  is the generator used for the pipeline demo; adapt its segment table and callouts.
- **Verify the file itself:** check it with ffprobe, transcribe the exported audio with `whisper-cli`
  (every scripted line present, at the right time), and make an ffmpeg contact sheet of the MP4.

## 5. Deliver

Always finish by publishing the final MP4 to the tailnet captures bucket and returning its link:

```sh
~/.claude/skills/screen-capture/scripts/publish.sh out/final.mp4 <slug>
# -> https://<host>.<tailnet>.ts.net/captures/<YYYY-MM-DD>-<slug>/final.mp4
```

- The bucket is `~/dev/captures/public/`. `scripts/serve_captures.py` serves it on `127.0.0.1:8740`, with Range
  support so Safari can play and seek. The LaunchAgent `dev.captures.serve` keeps the server running, and
  `tailscale serve --bg --set-path /captures http://127.0.0.1:8740` mounts it. The mount persists and is
  **tailnet-only**. `publish.sh` checks both and repairs them if needed.
- Browse everything published at `https://<host>.<tailnet>.ts.net/captures/` (newest first).
- Never switch this to `tailscale funnel` (public internet) without the user asking.
- Report the link plus duration, resolution and the script used. Give the link as a Markdown link.
- A public link through `cap upload out/final.mp4 --json` publishes externally, so confirm before running it.
