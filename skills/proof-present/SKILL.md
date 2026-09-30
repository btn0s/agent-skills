---
name: proof-present
description: >-
  Render and publish proof and walkthrough videos. Use when turning a proof.yaml into a narrated mp4 with the
  `proof` tool (terminal beats, charts, timelines, flows, cards, media, Kokoro voice, chapters), attaching it to a
  PR, or for a full Cap → Kokoro → Tesseract edit. The words come from proof-write, the recordings and data from
  proof-capture, and the tools from proof-setup.
---

# Presenting a proof: render → review → publish

The script (story, agenda, `say:` lines) comes from **proof-write**. The raw material (recordings, trace JSON) comes from **proof-capture**. This skill turns them into one video and a link.

## Setup

Run `~/.agents/skills/proof-setup/install.sh --check` first. The proof-setup skill has the details.

## Fast path: `proof` (use this first)

For PR proofs, choose the lowest tier that proves the change. One spec file becomes one command,
which gives you a published tailnet link. There's no screen recording, TCC or GUI involved:
terminal beats run in a real bash under a pty and are rendered frame by frame.

| Tier | When | Command | Typical time |
| --- | --- | --- | --- |
| 0 still | Proving a visual state exists | `proof shot [--window "App"] --slug x` | <1s |
| 1 raw | Terminal output is the proof, no polish | `proof run spec.yaml --raw` | ~10s |
| 2 narrated | The default for PRs: captions, callouts and a Kokoro voice | `proof run spec.yaml` | ~19s |
| 3 silent | Captions only, or no Kokoro on this host | `proof run spec.yaml --no-narrate` | ~13s |
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
    say: "On main, the two tests with accented titles fail."   # spoken line; defaults to the caption
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

Media beats put screenshots and recordings (Simulator, device, game capture) in the same video. Pick a layout per beat with `layout:`:

- `device` (default for video): the media is centred and fitted, and the heading and caption sit centred underneath it. Use this for phone and tablet captures in either orientation.
- `device-side`: portrait media on the right, with the heading and caption in a left column.
- `full` (default for images): the media fills the frame above the bottom caption. Use this for game captures and desktop screens.

```yaml
  - video: recordings/02-start.mp4     # or image: shots/after.png
    heading: "Start a session"          # optional; the PR step's bold heading
    caption: "The mock control plane walks provisioning to ready."
    trim: [0.5, 6]                      # optional, seconds
    speed: 1.5                          # optional
    rotate: ccw                         # optional: cw | ccw | 180
    layout: device                      # optional; see above
```

Simulator recordings are always in panel orientation, so a landscape run comes out sideways. `rotate: ccw` fixes a `LANDSCAPE_LEFT` run and `rotate: cw` fixes `LANDSCAPE_RIGHT`. Check one frame to confirm. Capturing them is covered in proof-capture.

Walkthroughs (a PR told as a story, not a single clip) use a few more pieces. Write the script with the proof-write skill; this section only covers the syntax.

- Subtitles are on whenever there's narration. The sentence being spoken appears centred at the bottom, one line at a time, and everything else moves up to make room. They're skipped where the caption already shows the same words. `proof.vtt` has the same text as a subtitle file. Turn them off only when asked, with `subtitles: false` or `--no-subtitles`.
- `pronounce: {written: spoken}` respells words for the voice only, while subtitles keep the written form, e.g. `"PR #446": pull request four forty-six`. Put project-wide terms in `proof.config.yaml`. Quote any YAML line containing ` #`, or YAML treats the rest as a comment.
- `say:` can be a list of sentences. Each one is voiced separately, and the lines on a card, the steps in a flow and the bars of a timeline appear as their sentence starts, so the screen never runs ahead of the voice.
- `card:` is a plain text page: `{title, body}`, where body is a string or a list of lines. With a `say:` list, line k appears on sentence k, and any extra leading sentences belong to the title. Cards ignore `heading`/`caption`.
- `card: {title, agenda: true}` lists every chapter name in order. On a chapter's own opener, that chapter is lit and the others are dimmed.
- `chapter: <name>` on any beat starts a chapter. The names become mp4 chapter markers, which players show as a jump list, and appear in the run's JSON as `chapters` with timestamps, ready to paste into the PR.
- `flow:` is a row of steps that explains a process before any numbers are shown: `{title, source, steps: [label | {label, at: k}], span: {from, to, label, at: k}}`. The span is a bracket under the part that was measured. `at: k` holds an item back until sentence k.
- `timeline:` is a stage waterfall. `runs: {name: {total, stages: [[stage, start, dur], ...]}}` goes inline or in `file:`. Two runs draw as before (gray) and after (accent). `show:` picks the runs on screen, `reveal:` picks the ones that sweep in (`[]` holds the chart still, for a focus beat), and `focus:` dims every other stage. `labels: {span_name: "Plain name"}` renames rows without editing the data. `dur: null` draws an open-ended bar, and `total` is optional.

Pull the numbers from the source (trace spans, benchmark JSON), never from a PR's chart image. Rebuild figures natively instead of pasting a screenshot of a white matplotlib chart.

Project defaults go in `proof.config.yaml` (or `.proof.yaml`). `proof` finds it by walking up from the spec to the repo root and puts it underneath the spec: spec keys win, and dict values merge one level deep. Put the house layout and capture quirks there, so each spec only holds the story:

```yaml
layouts: {video: device, image: device}
media: {rotate: ccw}                    # defaults for every image/video beat
```

`{ratio}` means the first series divided by the marked one at that x, so labels track the real numbers.
Terminal callouts accept `regex: true` for dynamic text, for example `find: "\\d+x(?= *$)"`.
Chart titles get the unit appended, e.g. "runtime vs. size (ms)". The line under the title is `source:`, which defaults to "Measured on <host>, <date>"; set it to the real conditions, for example `source: "M4 Pro · Python 3.13 · best of 3"`.
There is a full example in `~/.agents/skills/proof-setup/proof/examples/perf.yaml`, and `mkperf.sh` rebuilds its demo repo.

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
- `--attach` uploads the mp4 as a GitHub attachment (needs the `gh-attach` extension; `--repo owner/name`, defaulting to the current checkout). `proof attach FILE --repo owner/name` does the same for an existing video.
- `--pr N` attaches and writes `pr-comment.md`, which contains only the attachment URL on its own line, so GitHub plays it inline.
- `--post` comments via `gh`, but only on PRs authored by btn0s, and only after the user confirms.

The JSON output contains:
- `url`: the direct tailnet `proof.mp4` link, and `attachment`: the GitHub attachment URL. Only the video is published: no HTML page, and no text outside the video.
- `mp4`
- `contact_sheet`
- `callouts_not_found`
- per-beat placement
- timings

Where a video goes:
- **PRs, especially private repos:** use a GitHub attachment (`--pr N` or `proof attach`). On a private repo the URL only loads for people with access to the repo (logged out, it's a 404), so there's no public bucket to manage. Videos can be up to 10 MB on free plans and 100 MB on paid plans.
- **Quick looks inside the tailnet:** the default tailnet link.
- Never make the captures bucket public (`tailscale funnel`) for work videos, because anyone with the link could watch it.

**Always open `contact_sheet` before sharing.** If `callouts_not_found` is not empty, fix the `find` text.

Tips:
- Keep output short so the terminal crops small and the text renders large. Pipe noisy commands through `grep` or `tail`.
- Put `git switch` and other state setup in `setup:` or at the start of a beat. The recording is real, so the repo must actually be in the demonstrated state.
- Example specs are in `~/.agents/skills/proof-setup/proof/examples/` (copy them to `~/dev/proof-specs/`); `mkdemo.sh` rebuilds the demo repo.
- The tool is `~/.agents/skills/proof-setup/proof/proof.py` (PEP 723 uv script), run through the `proof` wrapper that proof-setup links onto PATH.


## Full edit: Cap → Kokoro → Tesseract

For marketing-grade demos that `proof` can't express. Three local tools, one pipeline:

| Stage | Tool | Skill with the details |
| --- | --- | --- |
| Record | `cap` (Cap Desktop CLI) | proof-capture, and `cap guide --json` |
| Narrate | Kokoro-82M via `mlx_audio.tts.generate` | `~/.agents/skills/proof-setup/scripts/narrate.py` |
| Annotate + edit + export | `tsrct` (Tesseract) | `tesseract-video`, `tesseract-motion` |

Read the linked skills before running their commands. This file is the order of operations, not a
replacement for them.

### 1. Plan (before recording)

Write `script.txt`, one narration beat per line. A beat is one action on screen plus the sentence spoken
over it. Optionally prefix a beat with the timestamp where it should start (`mm:ss.s |`). Without
timestamps, beats run back to back.

```
00:00.0 | This is the new settings panel.
00:04.5 | Click Integrations, then choose GitHub.
          Authorize, and the repo list fills in automatically.
```

Write the lines with proof-write. Keep beats short (at most about 12 words, 3–5 s each). Do an action, then narrate it. Never script claims the
recording doesn't show. Don't invent speech or captions: all narration comes from this script, which the user
approves.

### 2. Record

Record with Cap as described in proof-capture, and export to `raw/take1.mp4`.

### 3. Narrate with Kokoro

```sh
python3 ~/.agents/skills/proof-setup/scripts/narrate.py script.txt audio/ \
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

### 4. Annotate, assemble, export with Tesseract

If `tsrct` is missing or its version doesn't match `tesseract-video/references/cli-version.txt`, follow
`tesseract-video/references/installation.md`. Don't substitute another version.


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

#### Lessons from headless terminal demos

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
  text, groups and opacity keyframes. To iterate, restore the copy and re-apply. `~/.agents/skills/proof-setup/scripts/build_edit_example.py`
  is the generator used for the pipeline demo; adapt its segment table and callouts.
- **Verify the file itself:** check it with ffprobe, transcribe the exported audio with `whisper-cli`
  (every scripted line present, at the right time), and make an ffmpeg contact sheet of the MP4.

### 5. Deliver

Always finish by publishing the final MP4 to the tailnet captures bucket and returning its link:

```sh
~/.agents/skills/proof-setup/scripts/publish.sh out/final.mp4 <slug>
# -> https://<host>.<tailnet>.ts.net/captures/<YYYY-MM-DD>-<slug>/final.mp4
```

- The bucket is `~/dev/captures/public/`. `~/.agents/skills/proof-setup/scripts/serve_captures.py` serves it on `127.0.0.1:8740`, with Range
  support so Safari can play and seek. The LaunchAgent `dev.captures.serve` keeps the server running, and
  `tailscale serve --bg --set-path /captures http://127.0.0.1:8740` mounts it. The mount persists and is
  **tailnet-only**. `publish.sh` checks both and repairs them if needed.
- Browse everything published at `https://<host>.<tailnet>.ts.net/captures/` (newest first).
- Never switch this to `tailscale funnel` (public internet) without the user asking.
- Report the link plus duration, resolution and the script used. Give the link as a Markdown link.
- A public link through `cap upload out/final.mp4 --json` publishes externally, so confirm before running it.
