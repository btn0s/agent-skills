# /// script
# requires-python = ">=3.12"
# dependencies = ["pyte", "pillow", "pyyaml", "imageio-ffmpeg"]
# ///
"""proof — fast, headless proof videos for PRs.

  proof run  spec.yaml [--no-narrate] [--raw] [--no-publish] [--attach] [--pr N [--repo O/R] [--post]]
             beats are terminal commands (run:/type:) or animated charts (chart:), mixed freely
  proof shot [--screen ID | --window ID] [--slug S]
  proof clip --duration N [--screen ID | --window ID] [--slug S] [-- command ...]
  proof publish PATH [--slug S]
  proof attach FILE [--repo O/R]     upload as a GitHub attachment; prints the URL

`run` drives a real shell through a pty and renders the terminal itself (pyte + Pillow): no screen
recording, no TCC, exact timing, and callouts that find text in the terminal buffer instead of pixels.
"""
import argparse, array, bisect, datetime as dt, hashlib, html, json, math, os, pty, random, re, select
import shutil, subprocess, sys, tempfile, termios, fcntl, struct, time, urllib.parse, wave
from dataclasses import dataclass, field

import imageio_ffmpeg
import pyte
import yaml
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
BUCKET = os.path.expanduser("~/dev/captures/public")
TAILSCALE = shutil.which("tailscale") or next(
    (p for p in ("/usr/local/bin/tailscale", "/Applications/Tailscale.app/Contents/MacOS/Tailscale") if os.path.exists(p)),
    "tailscale")
CAP = os.path.expanduser("~/.cap/bin/cap")
TTS_PY = os.environ.get("PROOF_TTS_PY") or os.path.expanduser("~/.local/share/uv/tools/mlx-audio/bin/python")
CACHE = os.path.expanduser("~/.cache/proof")

W, H, FPS = 1920, 1080, 30
MONO = "/System/Applications/Utilities/Terminal.app/Contents/Resources/Fonts/SF-Mono-{}.otf"
UI = os.path.join(HERE, "fonts", "Inter-{}.ttf")

def hx(h):
    return tuple(int(h[k:k + 2], 16) for k in (1, 3, 5))


# Dark tokens from the dataviz reference palette. The data is the only loud thing on screen.
BG = hx("#111110")          # page and terminal surface, edge to edge (no window chrome)
FG = hx("#ffffff")          # primary ink
INK2 = hx("#c3c2b7")        # secondary ink
MUTED = hx("#898781")       # axis, prompt, captions
GRID = hx("#2c2c2a")        # hairline grid
AXIS = hx("#383835")        # baseline
ACCENT = hx("#3987e5")      # the one emphasis colour (after / the change)
BEFORE = hx("#898781")      # de-emphasised baseline series (before / main)
SERIES = [hx(h) for h in ("#3987e5", "#d95926", "#199e70", "#c98500", "#d55181")]
ANSI = {
    "black": AXIS, "red": hx("#e66767"), "green": hx("#1baf7a"), "brown": hx("#c98500"),
    "yellow": hx("#c98500"), "blue": hx("#3987e5"), "magenta": hx("#9085e9"), "cyan": hx("#1baf7a"),
    "white": INK2,
    "brightblack": MUTED, "brightred": hx("#e66767"), "brightgreen": hx("#1baf7a"),
    "brightbrown": hx("#eda100"), "brightyellow": hx("#eda100"), "brightblue": hx("#3987e5"),
    "brightmagenta": hx("#9085e9"), "brightcyan": hx("#1baf7a"), "brightwhite": FG,
}
MARGIN = 120                # one outer margin for terminal, chart and caption
CAP_BAND = 150              # reserved under the content for a caption line

def log(*a):
    print("[proof]", *a, file=sys.stderr, flush=True)


# ---------------------------------------------------------------- terminal capture

@dataclass
class Snap:
    t: float
    rows: list          # rows of (text, fg, bg, bold, reverse) per cell
    lines: list         # plain text per row, for find
    cursor: tuple       # (x, y, visible)


@dataclass
class Callout:
    find: str
    label: str
    on: float = 0.0
    off: float = 0.0
    cell: tuple = None  # (row, col0, col1)
    place: tuple = None  # ("right"|"below"|"above", row, col) or ("caption",)


@dataclass
class Beat:
    spec: dict
    start: float = 0.0
    done: float = 0.0
    end: float = 0.0
    voice: str = None
    voice_dur: float = 0.0
    callouts: list = field(default_factory=list)
    chart: dict = None
    media: dict = None
    timeline: dict = None
    card: dict = None
    flow: dict = None
    marks: list = field(default_factory=list)  # seconds after start when each spoken sentence begins

    def at(self, k):
        """When sentence k starts (reveals keyed to narration); past the last sentence, the beat's end."""
        return self.start + (self.marks[k] if k < len(self.marks) else self.end - self.start)

    @property
    def kind(self):
        for k in ("chart", "media", "timeline", "card", "flow"):
            if getattr(self, k):
                return k
        return "term"


class Term:
    def __init__(self, cols, rows, cwd, prompt, env_extra):
        self.cols, self.rows = cols, rows
        self.screen = pyte.Screen(cols, rows)
        self.stream = pyte.ByteStream(self.screen)
        rc = tempfile.NamedTemporaryFile("w", suffix=".bashrc", delete=False)
        rc.write(
            "unset PROMPT_COMMAND; HISTFILE=/dev/null\n"
            f"PS1='\\[\\e]0;PROOF_READY\\a\\]\\[\\e[90m\\]{prompt[1]} \\$\\[\\e[0m\\] '\n")
        rc.close()
        env = dict(os.environ, TERM="xterm-256color", COLUMNS=str(cols), LINES=str(rows),
                   BASH_SILENCE_DEPRECATION_WARNING="1", CLICOLOR_FORCE="1", FORCE_COLOR="1",
                   GIT_PAGER="cat", PAGER="cat", **env_extra)
        pid, fd = pty.fork()
        if pid == 0:
            os.chdir(cwd)
            os.execve("/bin/bash", ["bash", "--noprofile", "--rcfile", rc.name, "-i"], env)
        self.pid, self.fd = pid, fd
        fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
        self.raw = b""

    def _read(self, timeout):
        r, _, _ = select.select([self.fd], [], [], timeout)
        if not r:
            return b""
        try:
            data = os.read(self.fd, 65536)
        except OSError:
            return b""
        self.stream.feed(data)
        self.raw += data
        return data

    def wait_prompt(self, timeout=30):
        mark = len(self.raw)
        end = time.time() + timeout
        while time.time() < end:
            self._read(0.05)
            if b"PROOF_READY" in self.raw[mark:]:
                while self._read(0.03):
                    pass
                return True
        return False

    def snap(self, t):
        rows, lines = [], []
        for y in range(self.rows):
            line = self.screen.buffer[y]
            cells = []
            for x in range(self.cols):
                c = line[x]
                cells.append((c.data, c.fg, c.bg, c.bold, c.reverse))
            rows.append(cells)
            lines.append("".join(ch[0] or " " for ch in cells))
        cur = self.screen.cursor
        return Snap(t, rows, lines, (cur.x, cur.y, not cur.hidden))

    def close(self):
        # Drain before reaping: on macOS a pty child can't finish exiting while its output is unread.
        try:
            os.write(self.fd, b"exit\r")
        except OSError:
            pass
        end = time.time() + 2
        while time.time() < end:
            r, _, _ = select.select([self.fd], [], [], 0.1)
            if r:
                try:
                    if not os.read(self.fd, 65536):
                        break
                except OSError:
                    break
            elif os.waitpid(self.pid, os.WNOHANG)[0]:
                return
        os.close(self.fd)
        try:
            os.kill(self.pid, 9)
            os.waitpid(self.pid, 0)
        except (OSError, ChildProcessError):
            pass


def record_terminal(spec, beats, t0, narrate_durs):
    """Drive every beat through a real shell; returns snapshots and skip events on a virtual clock."""
    cols, rows = spec.get("size", [100, 22])
    cwd = os.path.expanduser(spec.get("cwd", "~"))
    prompt = spec.get("prompt", [f"{os.environ.get('USER', 'dev')}@devbox", "~/" + os.path.basename(cwd.rstrip("/"))])
    term = Term(cols, rows, cwd, prompt, {k: str(v) for k, v in spec.get("env", {}).items()})
    if not term.wait_prompt():
        raise SystemExit("shell never showed a prompt")
    for cmd in spec.get("setup", []):  # invisible: runs before the recording starts
        os.write(term.fd, (cmd + "\r").encode())
        term.wait_prompt(spec.get("timeout", 120))
    os.write(term.fd, b"clear\r")
    term.wait_prompt()
    rnd = random.Random(7)
    snaps, skips = [term.snap(t0)], []
    scenes = ("image", "video", "flow", "card", "timeline", "chart")
    opens_on_term = beats and not any(beats[0].spec.get(k) for k in scenes)
    t = t0 + (0.4 if opens_on_term else 0)  # a beat at 0 would otherwise flash an empty prompt first
    max_gap = float(spec.get("max_gap", 0.8))

    def push(s):
        if snaps and s.t - snaps[-1].t < 1 / FPS:
            snaps[-1] = s
        else:
            snaps.append(s)

    for i, b in enumerate(beats):
        s = b.spec
        if s.get("image") or s.get("video"):
            kind = "video" if s.get("video") else "image"
            layout = s.get("layout") or spec.get("layouts", {}).get(kind) or ("device" if kind == "video" else "full")
            if layout not in LAYOUTS:
                raise SystemExit(f"unknown layout {layout!r}; choose from {', '.join(LAYOUTS)}")
            s = {**spec.get("media", {}), **s}  # project-wide media defaults (rotate, speed...)
            b.media = load_media(s, os.path.dirname(os.path.abspath(spec["_path"])), cwd, layout)
            b.start = t
            b.done = t + b.media["dur"]
            cap_words = len(((s.get("heading") or "") + " " + (s.get("caption") or "")).split())
            hold = float(s.get("hold", 1.2 if s.get("video") else 2.2))
            b.end = max(b.done + hold, b.start + 1.0 + cap_words / 3.2, b.start + narrate_durs.get(i, 0) + 0.6)
            t = b.end
            continue
        if s.get("flow"):
            b.flow = dict(s["flow"])
            b.start = t
            b.done = t + 0.3
            b.end = max(b.start + float(s.get("hold", 3.0)), b.start + narrate_durs.get(i, 0) + 0.8)
            t = b.end
            continue
        if s.get("card"):
            c = s["card"] if isinstance(s["card"], dict) else {"title": s["card"]}
            body = c.get("body") or []
            body = [body] if isinstance(body, str) else list(body)
            current = None
            if c.get("agenda"):  # the chapter list; on a chapter opener the current chapter is lit
                body, current = list(spec["_agenda"]), s.get("chapter")
            b.card = {"title": c.get("title", ""), "body": body, "current": current, "agenda": bool(c.get("agenda"))}
            b.start = t
            b.done = t + 0.3
            words = len(" ".join([b.card["title"]] + b.card["body"]).split())
            b.end = max(b.start + float(s.get("hold", 1.4)) + words / 3.6, b.start + narrate_durs.get(i, 0) + 0.7)
            t = b.end
            continue
        if s.get("timeline"):
            b.timeline = load_timeline(s["timeline"], os.path.dirname(os.path.abspath(spec["_path"])), cwd)
            b.timeline["_reserve"] = text_reserve(s) // 2  # the plot's own axis labels already sit in the gap
            b.start = t
            b.done = t + b.timeline["draw"] + 0.2
            cap_words = len(((s.get("heading") or "") + " " + (s.get("caption") or "")).split())
            hold = float(s.get("hold", 2.4))
            b.end = max(b.done + hold, b.start + 1.0 + cap_words / 3.2, b.start + narrate_durs.get(i, 0) + 0.6)
            t = b.end
            continue
        if s.get("chart"):
            b.chart = load_chart(s["chart"], cwd, spec.get("env", {}))
            b.start = t
            b.done = t + CHART_DRAW + 0.2
            cap_words = len((s.get("caption") or "").split())
            hold = float(s.get("hold", 2.6 if b.chart["marks"] else 1.8))
            b.end = max(b.done + hold, b.start + 1.0 + cap_words / 3.2, b.start + narrate_durs.get(i, 0) + 0.6)
            t = b.end
            continue
        if s.get("clear") and i:
            os.write(term.fd, b"clear\r")
            term.wait_prompt()
            push(term.snap(t))
        b.start = t
        t += 0.45
        cmd = s.get("run") or s.get("type") or ""
        for ch in cmd:
            os.write(term.fd, ch.encode())
            term._read(0.2)
            while term._read(0.004):
                pass
            t += 0.022 + rnd.random() * 0.024 + (0.08 if ch == " " and rnd.random() < 0.25 else 0)
            push(term.snap(t))
        if s.get("run") is not None:
            t += 0.25
            os.write(term.fd, b"\r")
            start_real = last_real = time.time()
            mark = len(term.raw)
            deadline = start_real + float(s.get("timeout", spec.get("timeout", 120)))
            while time.time() < deadline:
                if not term._read(0.05):
                    if b"PROOF_READY" in term.raw[mark:]:
                        break
                    continue
                now = time.time()
                gap = now - last_real
                last_real = now
                if gap > max_gap:
                    skips.append((t + max_gap, gap - max_gap))
                t += min(gap, max_gap)
                push(term.snap(t))
                if b"PROOF_READY" in term.raw[mark:]:
                    while term._read(0.03):
                        pass
                    push(term.snap(t))
                    break
            else:
                log(f"beat {i + 1}: timed out waiting for {cmd!r}")
        b.done = t
        cap_words = len((s.get("caption") or "").split())
        hold = float(s.get("hold", 2.6 if s.get("callout") else 1.6))
        b.end = max(b.done + hold, b.start + 1.0 + cap_words / 3.2, b.start + narrate_durs.get(i, 0) + 0.6)
        t = b.end
    term.close()
    return snaps, skips, t


# ---------------------------------------------------------------- narration

def synthesize(lines, voice, speed):
    """lines: {idx: text} -> {idx: (wav_path, seconds)}; cached by content hash."""
    os.makedirs(os.path.join(CACHE, "tts"), exist_ok=True)
    out, jobs = {}, []
    for i, text in lines.items():
        key = hashlib.sha1(f"{voice}|{speed}|{text}".encode()).hexdigest()[:16]
        path = os.path.join(CACHE, "tts", f"{key}.wav")
        out[i] = path
        if not os.path.exists(path):
            jobs.append({"text": text, "out": path, "voice": voice, "speed": speed, "lang": voice[0]})
    if jobs:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(jobs, f)
        subprocess.run([TTS_PY, os.path.join(HERE, "tts_batch.py"), f.name], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    res = {}
    for i, path in out.items():
        with wave.open(path) as w:
            res[i] = (path, w.getnframes() / w.getframerate())
    return res


SENTENCE_GAP = 0.35


def join_wavs(paths, out, gap):
    rate, pcm = None, b""
    for k, p in enumerate(paths):
        with wave.open(p) as w:
            rate = rate or w.getframerate()
            pcm += (b"\0\0" * int(gap * rate) if k else b"") + w.readframes(w.getnframes())
    with wave.open(out, "wb") as w:
        w.setnchannels(1), w.setsampwidth(2), w.setframerate(rate)
        w.writeframes(pcm)
    return len(pcm) / 2 / rate


def mix_audio(beats, total, path):
    rate = 24000
    buf = array.array("i", [0]) * int((total + 1) * rate)
    for b in beats:
        if not b.voice:
            continue
        with wave.open(b.voice) as w:
            assert w.getframerate() == rate and w.getsampwidth() == 2
            samples = array.array("h", w.readframes(w.getnframes()))
        off = int((b.start + 0.15) * rate)
        for k, v in enumerate(samples):
            if off + k < len(buf):
                buf[off + k] += v
    pcm = array.array("h", (max(-32768, min(32767, v)) for v in buf))
    with wave.open(path, "wb") as w:
        w.setnchannels(1), w.setsampwidth(2), w.setframerate(rate)
        w.writeframes(pcm.tobytes())


# ---------------------------------------------------------------- rendering

def ink(col, a, bg=None):
    """Text colour faded toward the page. Pillow ignores alpha when drawing text onto an RGB image."""
    bg = BG if bg is None else bg
    return tuple(round(b + (c - b) * a) for c, b in zip(col, bg))


def font(kind, size):
    """kind: "mono" / "mono-bold" for the terminal, or an Inter weight (Bold, SemiBold, Medium)."""
    if kind.startswith("mono"):
        return ImageFont.truetype(MONO.format("Bold" if kind == "mono-bold" else "Regular"), size)
    return ImageFont.truetype(UI.format(kind), size)


def color(c, default):
    if c in (None, "default"):
        return default
    if c in ANSI:
        return ANSI[c]
    if isinstance(c, str) and re.fullmatch(r"[0-9a-fA-F]{6}", c):
        return tuple(int(c[k:k + 2], 16) for k in (0, 2, 4))
    return default


# ---------------------------------------------------------------- charts

CHART_DRAW, XFADE, DIM = 1.2, 0.3, 0.3
U = 2  # video px per design px: the 1920 frame is viewed around 960 wide in a PR


def load_chart(c, cwd, env):
    """Chart data comes from a real command (cmd:) or a file an earlier beat wrote (file:), as JSON:
    {"x": [...], "series": {"name": [...], ...}, "unit": "ms", "marks": [{"series", "x", "label"}]}"""
    if c.get("cmd"):
        out = subprocess.run(c["cmd"], shell=True, cwd=cwd, capture_output=True, text=True, check=True,
                             env=dict(os.environ, **{k: str(v) for k, v in env.items()})).stdout
        data = json.loads(out)
    elif c.get("file"):
        data = json.load(open(os.path.join(cwd, os.path.expanduser(c["file"]))))
    else:
        data = {k: c[k] for k in ("x", "series") if k in c}
    d = {**data, **{k: v for k, v in c.items() if k not in ("cmd", "file")}}
    d.setdefault("kind", "line")
    d["marks"] = list(data.get("marks", [])) + list(c.get("marks", []))
    ys = [v for vs in d["series"].values() for v in vs]
    for m in d["marks"]:  # "{ratio}" in a label = first series / this series at that x
        j = d["x"].index(m["x"])
        first = next(iter(d["series"].values()))[j]
        mine = d["series"][m["series"]][j]
        m["label"] = m["label"].format(ratio=first / mine if mine else float("inf"), value=mine)
    d["ymax"] = max(ys) if ys else 1
    d.setdefault("source", f"Measured on {os.uname().nodename.split('.')[0]}, {dt.date.today():%Y-%m-%d}")
    return d


def series_colors(names):
    """Two series read as before -> after: gray baseline, one accent. More use the categorical order."""
    if len(names) == 2:
        return [BEFORE, ACCENT]
    return [SERIES[k % len(SERIES)] for k in range(len(names))]


def nice_ticks(vmax, n=4):
    raw = vmax / n
    mag = 10 ** math.floor(math.log10(raw))
    step = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw)
    return [k * step for k in range(int(math.ceil(vmax / step - 1e-9)) + 1)]


def fmt_num(v):
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "k")):
        if abs(v) >= div:
            return f"{v / div:.3g}{suf}"
    return f"{v:,.3g}" if abs(v) < 1000 else f"{v:,.0f}"


def draw_chart(c, p, mark_a):
    """One chart state, drawn at 2x and downsampled for clean lines. p: draw-in 0..1, mark_a: label fade."""
    S = 2
    im = Image.new("RGB", (W * S, H * S), BG)
    d = ImageDraw.Draw(im, "RGBA")
    k = S * U  # design px -> supersampled px
    f_title, f_sub = font("SemiBold", 22 * k), font("Medium", 13 * k)
    f_tick, f_val = font("Medium", 12 * k), font("SemiBold", 14 * k)
    x0, y0 = MARGIN * S, MARGIN * S * 0.75
    unit = c.get("unit", "")
    title = c.get("title", "")
    if unit and f"({unit})" not in title:
        title = f"{title} ({unit})" if title else unit
    d.text((x0, y0), title, font=f_title, fill=FG)
    d.text((x0, y0 + 32 * k), c["source"], font=f_sub, fill=MUTED)
    names = list(c["series"])
    cols = series_colors(names)
    lx = x0
    ly = y0 + 60 * k
    for name, col in zip(names, cols):  # legend: line-key + label, one row
        d.line((lx, ly + 8 * k, lx + 16 * k, ly + 8 * k), fill=col, width=2 * k)
        d.ellipse((lx + 4 * k, ly + 4 * k, lx + 12 * k, ly + 12 * k), fill=col)
        d.text((lx + 24 * k, ly - 1 * k), name, font=f_sub, fill=INK2)
        lx += 24 * k + f_sub.getlength(name) + 28 * k
    ticks = nice_ticks(c["ymax"])
    tick_w = max(f_tick.getlength(fmt_num(v)) for v in ticks)
    fmt_v = lambda v: f"{fmt_num(v)} {unit}".strip()
    marks = {(m["series"], m["x"]): m["label"] for m in c["marks"]}
    gutter = 0
    if c["kind"] not in ("bar", "column"):  # end labels sit right of the plot; size the gutter to fit them
        for name in names:
            lab = c["series"][name][-1]
            m = marks.get((name, c["x"][-1]))
            gutter = max(gutter, f_val.getlength(fmt_v(lab)) + (f_val.getlength(m) + 10 * k if m else 0))
        gutter += 24 * k
    px0, px1 = x0 + tick_w + 14 * k, W * S - MARGIN * S - gutter
    py0, py1 = ly + 44 * k, (H - MARGIN - CAP_BAND - 20) * S  # keep the caption band clear
    top = ticks[-1]
    Y = lambda v: py1 - (py1 - py0) * v / top
    for v in ticks:
        d.line((px0, Y(v), px1, Y(v)), fill=AXIS if v == 0 else GRID, width=max(1, k // 2))
        lab = fmt_num(v)
        d.text((px0 - 14 * k - f_tick.getlength(lab), Y(v) - 8 * k), lab, font=f_tick, fill=MUTED)
    xs, n = c["x"], len(c["x"])
    bar = c["kind"] in ("bar", "column")
    slot = (px1 - px0) / (n if bar else max(n - 1, 1))
    X = (lambda j: px0 + slot * (j + 0.5)) if bar else (lambda j: px0 + slot * j)
    for j, xv in enumerate(xs):
        lab = fmt_num(xv) if isinstance(xv, (int, float)) else str(xv)
        d.text((X(j) - f_tick.getlength(lab) / 2, py1 + 10 * k), lab, font=f_tick, fill=MUTED)
    if c.get("x_label"):
        d.text((px1 - f_tick.getlength(c["x_label"]), py1 + 30 * k), c["x_label"], font=f_tick, fill=MUTED)
    ends = []
    for si, (name, col) in enumerate(zip(names, cols)):
        ys = c["series"][name]
        if bar:
            bw = min(24 * k, slot * 0.7 / len(names))
            gap = 2 * k
            gx = X(0) - (bw * len(names) + gap * (len(names) - 1)) / 2
            for j, v in enumerate(ys):
                bx = X(j) - (bw * len(names) + gap * (len(names) - 1)) / 2 + si * (bw + gap)
                h = (py1 - Y(v)) * p
                if h > 1:
                    d.rounded_rectangle((bx, py1 - h, bx + bw, py1), 4 * k, fill=col, corners=(True, True, False, False))
                if (name, xs[j]) in marks or j == n - 1:
                    ends.append((bx + bw / 2, py1 - h, fmt_v(v), marks.get((name, xs[j])), "top"))
            continue
        reach = p * (n - 1)
        path = [(X(j), Y(v)) for j, v in enumerate(ys) if j <= reach]
        jf = int(reach)
        if jf < n - 1 and reach > jf:
            u = reach - jf
            path.append((X(jf) + slot * u, Y(ys[jf] + (ys[jf + 1] - ys[jf]) * u)))
        if len(path) > 1:
            d.line(path, fill=col, width=2 * k, joint="curve")
        for j, v in enumerate(ys):
            if j <= reach + 1e-9:
                r = 4 * k
                d.ellipse((X(j) - r - 2 * k, Y(v) - r - 2 * k, X(j) + r + 2 * k, Y(v) + r + 2 * k), fill=BG)
                d.ellipse((X(j) - r, Y(v) - r, X(j) + r, Y(v) + r), fill=col)
        ends.append((X(n - 1), Y(ys[-1]), fmt_v(ys[-1]), marks.get((name, xs[-1])), "right"))
    if p >= 1:  # direct labels only at the ends, text in ink (never the series colour)
        ends.sort(key=lambda e: e[1])
        last_y = -1e9
        for ex, ey, val, mark, side in ends:
            if side == "right":
                ty = max(ey - 10 * k, last_y + 22 * k)
                last_y = ty
                d.text((ex + 14 * k, ty), val, font=f_val, fill=FG)
                if mark:
                    mx = ex + 14 * k + f_val.getlength(val) + 10 * k
                    d.text((mx, ty + 1 * k), mark, font=f_val, fill=ink(INK2, mark_a))
            else:
                d.text((ex - f_val.getlength(val) / 2, ey - 24 * k), val, font=f_val, fill=FG)
                if mark:
                    d.text((ex - f_sub.getlength(mark) / 2, ey - 44 * k), mark, font=f_sub, fill=ink(INK2, mark_a))
    return im.resize((W, H), Image.LANCZOS)


# ---------------------------------------------------------------- timelines (stage waterfalls, before vs after)

def load_timeline(c, spec_dir, cwd):
    """Stage waterfall. runs: {name: {total, stages: [[stage, start, dur], ...]}} inline or from file: (same JSON).
    show: the runs on screen (default all); reveal: the runs that draw in (default all shown); focus: stage(s) to keep
    lit while the rest dims. Two runs read as before (gray) and after (accent)."""
    data = {}
    if c.get("file"):
        f = os.path.expanduser(c["file"])
        data = json.load(open(next((q for q in (os.path.join(spec_dir, f), os.path.join(cwd, f)) if os.path.exists(q)), f)))
    d = {**data, **{k: v for k, v in c.items() if k != "file"}}
    runs = d["runs"]
    d["show"] = list(d.get("show") or runs)
    d["reveal"] = list(d["show"]) if d.get("reveal") is None else list(d["reveal"])  # reveal: [] = all static
    focus = d.get("focus") or []
    d["focus"] = [focus] if isinstance(focus, str) else list(focus)
    d["rows"] = list(d.get("rows") or dict.fromkeys(st[0] for r in runs.values() for st in r["stages"]))
    d["xmax"] = float(d.get("xmax") or max(r.get("total") or max(a + (du or 0) for _, a, du in r["stages"])
                                           for r in runs.values()) * 1.04)
    d["draw"] = float(d.get("draw", 2.2))
    d.setdefault("unit", "s")
    d.setdefault("source", f"Measured on {os.uname().nodename.split('.')[0]}, {dt.date.today():%Y-%m-%d}")
    return d


def draw_timeline(c, p, focus_a):
    """p: 0..1 sweep of the revealed runs along the time axis; focus_a: 0..1 dimming of unfocused rows."""
    S = 2
    im = Image.new("RGB", (W * S, H * S), BG)
    d = ImageDraw.Draw(im, "RGBA")
    k = S * U
    f_title, f_sub = font("SemiBold", 22 * k), font("Medium", 13 * k)
    f_tick, f_row, f_val = font("Medium", 12 * k), font("Medium", 13 * k), font("SemiBold", 13 * k)
    x0, y0 = MARGIN * S, MARGIN * S * 0.75
    unit = c["unit"]
    title = c.get("title", "")
    if unit and f"({unit})" not in title:
        title = f"{title} ({unit})"
    d.text((x0, y0), title, font=f_title, fill=FG)
    d.text((x0, y0 + 32 * k), c["source"], font=f_sub, fill=MUTED)
    names = list(c["runs"])
    cols = dict(zip(names, series_colors(names)))
    shown = [n for n in names if n in c["show"]]
    lx, ly = x0, y0 + 60 * k
    for name in shown:  # legend
        d.rounded_rectangle((lx, ly + 3 * k, lx + 14 * k, ly + 13 * k), 2 * k, fill=cols[name])
        d.text((lx + 22 * k, ly - 1 * k), name, font=f_sub, fill=INK2)
        lx += 22 * k + f_sub.getlength(name) + 28 * k
    rows = c["rows"]
    rname = lambda r: c.get("labels", {}).get(r, r)  # plain-language row names; the data keeps the trace's
    label_w = max(f_row.getlength(rname(r)) for r in rows)
    px0, px1 = x0 + label_w + 24 * k, W * S - MARGIN * S - 80 * k
    py0, py1 = ly + 52 * k, (H - MARGIN - CAP_BAND - 20 - c.get("_reserve", 0)) * S
    X = lambda v: px0 + (px1 - px0) * v / c["xmax"]
    ticks = nice_ticks(c["xmax"], 5)
    for v in ticks:
        if v > c["xmax"]:
            continue
        d.line((X(v), py0 - 8 * k, X(v), py1), fill=AXIS if v == 0 else GRID, width=max(1, k // 2))
        lab = f"{fmt_num(v)} {unit}" if v == ticks[-1] or X(ticks[-1]) > px1 and v == ticks[-2] else fmt_num(v)
        d.text((X(v) - f_tick.getlength(lab) / 2, py1 + 10 * k), lab, font=f_tick, fill=MUTED)
    row_h = (py1 - py0) / len(rows)
    lane = min(16 * k, (row_h - 10 * k) / max(len(shown), 1))
    cursor = c["xmax"] * p
    lit = lambda r: not c["focus"] or r in c["focus"]
    for ri, r in enumerate(rows):
        dim = 0 if lit(r) else 0.6 * focus_a
        cy = py0 + row_h * (ri + 0.5)
        d.text((px0 - 24 * k - f_row.getlength(rname(r)), cy - 9 * k), rname(r), font=f_row, fill=mix(INK2, BG, dim))
        top = cy - lane * len(shown) / 2
        for li, name in enumerate(shown):
            st = next((x for x in c["runs"][name]["stages"] if x[0] == r), None)
            if not st:
                continue
            a, du = st[1], st[2]
            open_end = du is None
            du = c["xmax"] - a if open_end else du
            z = a + du if name not in c["reveal"] else min(a + du, cursor)
            if z <= a and du > 0:
                continue
            by0, by1 = top + lane * li + 1.5 * k, top + lane * (li + 1) - 1.5 * k
            d.rounded_rectangle((X(a), by0, max(X(z), X(a) + 2 * k), by1), 2 * k, fill=mix(cols[name], BG, dim))
            crowded = len(shown) > 1 and c["focus"] and not lit(r)  # paired lanes: label only the stages in focus
            if z >= a + du and not open_end and not crowded:  # duration label once the bar is complete
                lab = f"{du:.2f} {unit}"
                d.text((max(X(z), X(a) + 2 * k) + 8 * k, (by0 + by1) / 2 - 8 * k), lab, font=f_val,
                       fill=mix(FG, BG, dim if lit(r) else max(dim, 0.35)))
    for name in shown:  # total marker per run: a hairline and the claim-to-ready number
        tot = c["runs"][name].get("total")
        if tot is None or name in c["reveal"] and cursor < tot:
            continue
        d.line((X(tot), py0 - 8 * k, X(tot), py1), fill=cols[name], width=max(2, k))
        lab = f"{fmt_num(round(tot, 1))} {unit}"
        d.text((X(tot) + 8 * k, py0 - 26 * k), lab, font=f_val, fill=FG)
    return im.resize((W, H), Image.LANCZOS)


# ---------------------------------------------------------------- media (screenshots, device and simulator recordings)

MEDIA_RADIUS = 36


# Layout library. A beat picks one with `layout:`; projects set defaults in proof.config.yaml.
#   device       media centred, heading + caption centred underneath (device and simulator recordings)
#   device-side  portrait media on the right, heading + caption in a left column
#   full         media fills the frame above a bottom-left caption (screenshots, game captures)
LAYOUTS = ("device", "device-side", "full")
CAP_UNDER = 190  # room under centred media for a heading and two caption lines


def text_reserve(s):
    """Extra px under a chart or full-frame media for a heading and a second caption line."""
    return (48 * U if s.get("heading") else 0) + (30 * U if len(s.get("caption") or "") > 95 else 0)


def media_box(w, h, layout, reserve=0):
    if layout == "device-side":
        bh = H - 2 * int(MARGIN * 0.6)
        bw = round(w * bh / h)
        return (W - MARGIN - bw, int(MARGIN * 0.6), bw, bh)
    if layout == "device":
        top = int(MARGIN * 0.6)
        scale = min((W - 2 * MARGIN) / w, (H - 2 * top - CAP_UNDER) / h)
        fw, fh = round(w * scale), round(h * scale)
        return ((W - fw) // 2, top + (H - 2 * top - CAP_UNDER - fh) // 2, fw, fh)
    bw, bh = W - 2 * MARGIN, H - 2 * MARGIN - CAP_BAND - reserve
    scale = min(bw / w, bh / h)
    fw, fh = round(w * scale), round(h * scale)
    return ((W - fw) // 2, MARGIN + (bh - fh) // 2, fw, fh)


ROTATIONS = {None: None, "cw": (Image.ROTATE_270, "transpose=1"), "ccw": (Image.ROTATE_90, "transpose=2"),
             "180": (Image.ROTATE_180, "hflip,vflip")}


def load_media(s, spec_dir, cwd, layout):
    """image: or video: beats. Videos are decoded once at FPS and sized to their box; trim: [a, b], speed: and rotate: apply.
    rotate: cw | ccw | 180 turns the source upright first. Simulator recordings are always in panel orientation, so a
    landscape run comes out sideways."""
    src = s.get("video") or s.get("image")
    path = next((p for p in (os.path.join(spec_dir, os.path.expanduser(src)), os.path.join(cwd, os.path.expanduser(src)))
                 if os.path.exists(p)), None)
    if not path:
        raise SystemExit(f"media not found: {src}")
    rot = None if s.get("rotate") is None else str(s["rotate"])
    if rot not in ROTATIONS:
        raise SystemExit(f"rotate must be one of {', '.join(k for k in ROTATIONS if k)}")
    if s.get("image"):
        im = Image.open(path).convert("RGB")
        if rot:
            im = im.transpose(ROTATIONS[rot][0])
        x, y, w, h = media_box(*im.size, layout, text_reserve(s))
        return {"frames": [im.resize((w, h), Image.LANCZOS)], "box": (x, y), "size": (w, h), "layout": layout,
                "dur": 0.0, "rounded": layout != "full"}
    probe = subprocess.run([FFMPEG, "-i", path], capture_output=True, text=True).stderr
    m = re.search(r", (\d{2,5})x(\d{2,5})", probe)
    sw, sh = int(m.group(1)), int(m.group(2))
    if rot in ("cw", "ccw"):
        sw, sh = sh, sw
    x, y, w, h = media_box(sw, sh, layout, text_reserve(s))
    out = tempfile.mkdtemp(prefix="proof-media-")
    a, z = (s.get("trim") or [0, None]) + [None] * (2 - len(s.get("trim") or [0, None]))
    speed = float(s.get("speed", 1))
    cmd = [FFMPEG, "-v", "error", "-y"] + (["-ss", str(a)] if a else []) + (["-to", str(z)] if z else []) + ["-i", path]
    vf = f"setpts=PTS/{speed},fps={FPS},{ROTATIONS[rot][1] + ',' if rot else ''}scale={w}:{h}:flags=lanczos"
    subprocess.run(cmd + ["-vf", vf, "-an", os.path.join(out, "%05d.png")], check=True)
    frames = sorted(os.path.join(out, f) for f in os.listdir(out))
    return {"frames": frames, "box": (x, y), "size": (w, h), "layout": layout, "dur": len(frames) / FPS,
            "rounded": layout != "full"}


_mask_cache = {}


def paste_media(im, frame, box, rounded):
    if isinstance(frame, str):
        frame = Image.open(frame).convert("RGB")
    if not rounded:
        im.paste(frame, box)
        return
    key = frame.size
    if key not in _mask_cache:  # supersampled rounded mask, so the corners stay smooth
        big = Image.new("L", (frame.width * 2, frame.height * 2), 0)
        ImageDraw.Draw(big).rounded_rectangle((0, 0, big.width - 1, big.height - 1), MEDIA_RADIUS * 2, fill=255)
        _mask_cache[key] = big.resize(frame.size, Image.LANCZOS)
    im.paste(frame, box, _mask_cache[key])


class Layout:
    """Terminal text sits straight on the page: no window, one margin, block centred in the space above the caption."""
    def __init__(self, cols, rows, raw):
        self.raw, self.cols, self.rows = raw, cols, rows
        max_w = W - 2 * MARGIN
        max_h = H - 2 * MARGIN - (0 if raw else CAP_BAND)
        size = 34
        while size > 12:
            f = font("mono", size)
            cw, lh = f.getlength("M"), round(size * 1.45)
            if cols * cw <= max_w and rows * lh <= max_h:
                break
            size -= 1
        self.size, self.cw, self.lh = size, cw, lh
        self.f, self.fb = font("mono", size), font("mono-bold", size)
        self.cx = MARGIN
        self.cy = MARGIN + max(0, (max_h - rows * lh) // 2)
        self.cap_y = H - MARGIN - 20

    def cell(self, row, col):
        return self.cx + col * self.cw, self.cy + row * self.lh


def wrap(text, f, max_w):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        nxt = (cur + " " + w_).strip()
        if f.getlength(nxt) <= max_w or not cur:
            cur = nxt
        else:
            lines.append(cur)
            cur = w_
    return lines + ([cur] if cur else [])


def mix(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


class Renderer:
    def __init__(self, spec, L, beats, snaps, skips, t_term0, t_term1, raw, title_card):
        self.spec, self.L, self.beats, self.snaps, self.skips = spec, L, beats, snaps, skips
        self.t_term0, self.t_term1, self.raw, self.title_card = t_term0, t_term1, raw, title_card
        self.snap_t = [s.t for s in snaps]
        self.f_cap = font("Medium", 17 * U)
        self.f_head = font("SemiBold", 19 * U)
        self.f_head_big = font("SemiBold", 40 * U)
        self.f_label = font("Medium", max(16, round(L.size * 0.82)))
        self.f_small = font("Medium", 12 * U)
        self.chart_cache = {}

    def snap_at(self, t):
        return self.snaps[max(0, bisect.bisect_right(self.snap_t, t) - 1)]

    def beat_at(self, t):
        for i, b in enumerate(self.beats):
            if b.start <= t < b.end:
                return i, b
        return None, None

    def focus(self, b, t):
        """While a callout shows, every row without a match fades toward the page."""
        if not b or not b.callouts:
            return set(), 0.0
        live = [c for c in b.callouts if c.cell and c.on <= t < c.off]
        if not live:
            return set(), 0.0
        a = min(1.0, (t - min(c.on for c in live)) / 0.25) * 0.55
        return {c.cell[0] for c in live}, a

    def terminal(self, t, b=None):
        L, s = self.L, self.snap_at(t)
        im = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(im)
        keep, dim = self.focus(b, t)
        for y, cells in enumerate(s.rows[:L.rows]):
            cells = cells[:L.cols]
            fade = dim if keep and y not in keep else 0.0
            x = 0
            while x < len(cells):
                ch, fg, bg, bold, rev = cells[x]
                run, x1 = [ch or " "], x + 1
                while x1 < len(cells) and cells[x1][1:] == (fg, bg, bold, rev):
                    run.append(cells[x1][0] or " ")
                    x1 += 1
                fgc, bgc = color(fg, INK2), color(bg, None)
                if bold and fg in (None, "default"):
                    fgc = FG
                if rev:
                    fgc, bgc = bgc or BG, fgc
                if fade:
                    fgc = mix(fgc, BG, fade)
                    bgc = bgc and mix(bgc, BG, fade)
                px, py = L.cell(y, x)
                if bgc:
                    d.rectangle((px, py, px + (x1 - x) * L.cw, py + L.lh), fill=bgc)
                text = "".join(run)
                if text.strip():
                    d.text((px, py + (L.lh - L.size) / 2 - 2), text, font=L.fb if bold else L.f, fill=fgc)
                x = x1
        cx, cy, vis = s.cursor
        if vis and (t * 1.6) % 1 < 0.72 and not keep:
            px, py = L.cell(cy, cx)
            d.rectangle((px, py + 4, px + L.cw, py + L.lh - 4), fill=INK2)
        return im

    def overlays(self, im, t):
        if self.raw:
            return im
        L, d = self.L, ImageDraw.Draw(im, "RGBA")
        i, b = self.beat_at(t)
        for vt, secs in self.skips:
            if vt <= t < vt + 1.8 and secs >= 1.5:
                txt = f"{secs:.0f} s of waiting cut"
                d.text((W - MARGIN - self.f_small.getlength(txt), MARGIN * 0.5), txt, font=self.f_small, fill=MUTED)
        extra = []
        if b and (b.card or b.flow):
            return im
        if b:
            for c in b.callouts:
                if not (c.on <= t < c.off) or not c.cell:
                    continue
                a = min(1.0, (t - c.on) / 0.25)
                row, c0, c1 = c.cell
                x0, y0 = L.cell(row, c0)
                x1, _ = L.cell(row, c1)
                d.rectangle((x0, y0 + L.lh - 6, x1, y0 + L.lh - 3), fill=ACCENT + (int(255 * a),))
                if not c.label:
                    continue
                if c.place[0] == "caption":
                    extra.append(c.label)
                    continue
                _, prow, pcol = c.place
                lx, ly = L.cell(prow, pcol)
                d.text((lx + L.cw * 0.5, ly + (L.lh - self.f_label.size) / 2 - 3), c.label, font=self.f_label,
                       fill=ink(FG, a))
            cap = " · ".join(extra + ([b.spec["caption"]] if b.spec.get("caption") else []))
            head = b.spec.get("heading")
            if b.media and b.media["layout"] == "device":
                (mx, my), (mw, mh) = b.media["box"], b.media["size"]
                y = my + mh + 28 * U / 2
                if head:
                    d.text(((W - self.f_head.getlength(head)) / 2, y), head, font=self.f_head, fill=FG)
                    y += self.f_head.size + 16
                for line in (wrap(cap, self.f_cap, min(W - 2 * MARGIN, 700 * U)) if cap else [])[:2]:
                    d.text(((W - self.f_cap.getlength(line)) / 2, y), line, font=self.f_cap, fill=INK2)
                    y += round(self.f_cap.size * 1.4)
                return im
            if b.media and b.media["layout"] == "device-side":
                col = min(b.media["box"][0] - 2 * MARGIN, 440 * U)
                hl = wrap(head, self.f_head_big, col) if head else []
                cl = wrap(cap, self.f_cap, col) if cap else []
                block = len(hl) * 52 * U / 1 + (16 * U if hl and cl else 0) + len(cl) * 30 * U
                y = (H - block) / 2
                for line in hl:
                    d.text((MARGIN, y), line, font=self.f_head_big, fill=FG)
                    y += 52 * U
                y += 16 * U if hl and cl else 0
                for line in cl:
                    d.text((MARGIN, y), line, font=self.f_cap, fill=INK2)
                    y += 30 * U
                return im
            if head:
                cap_lines = wrap(cap, self.f_cap, W - 2 * MARGIN) if cap else []
                y = L.cap_y - 30 * U * len(cap_lines) - self.f_head.size - 8 * U
                d.text((MARGIN, y), head, font=self.f_head, fill=FG)
            if cap:
                lines = wrap(cap, self.f_cap, W - 2 * MARGIN)
                y = L.cap_y - 30 * U * (len(lines) - 1) - self.f_cap.size
                for k, line in enumerate(lines):
                    d.text((MARGIN, y + 30 * U * k), line, font=self.f_cap, fill=INK2)
        return im

    def card(self, kind="title"):
        im = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(im)
        f_big, f_sub = font("SemiBold", 34 * U), font("Medium", 17 * U)
        lines = wrap(self.spec.get("title", ""), f_big, W - 2 * MARGIN)
        y = H * 0.42 - 48 * U * len(lines) / 2
        for line in lines:
            d.text((MARGIN, y), line, font=f_big, fill=FG)
            y += 48 * U
        if self.spec.get("subtitle"):
            d.text((MARGIN, y + 10 * U), self.spec["subtitle"], font=f_sub, fill=MUTED)
        return im

    def chart_frame(self, b, t):
        u = min(max((t - b.start) / CHART_DRAW, 0), 1)
        p = 1 if u >= 1 else 1 - (1 - u) ** 3
        mark_a = min(1.0, max(0.0, (t - b.done + 0.05) / 0.3))
        key = (id(b), round(p, 3), round(mark_a, 2))
        if key not in self.chart_cache:
            self.chart_cache[key] = draw_chart(b.chart, p, mark_a)
        return self.chart_cache[key].copy()

    def timeline_frame(self, b, t):
        c = b.timeline
        u = min(max((t - b.start) / c["draw"], 0), 1)
        p = 1 if u >= 1 else 1 - (1 - u) ** 2
        fa = min(1.0, max(0.0, (t - b.done + 0.05) / 0.4)) if c["focus"] else 0
        key = (id(b), round(p, 3), round(fa, 2))
        if key not in self.chart_cache:
            self.chart_cache[key] = draw_timeline(c, p, fa)
        return self.chart_cache[key].copy()

    def reveal_alpha(self, b, n_items, k, t):
        """Items appear as they're spoken: with a say: list, item k shows when its sentence starts
        (sentences beyond the items belong to the title). Otherwise everything shows at once."""
        if len(b.marks) < 2:
            return 1.0
        off = max(0, len(b.marks) - n_items)
        return min(1.0, max(0.0, (t - b.at(k + off)) / 0.3))

    def card_frame(self, b, t):
        """Intro, chapter, agenda and outro cards: a heading and plain lines, left-aligned on the page."""
        c = b.card
        alphas = tuple(round(self.reveal_alpha(b, len(c["body"]), k, t), 2) for k in range(len(c["body"])))
        key = (id(b), alphas)
        if key not in self.chart_cache:
            im = Image.new("RGB", (W, H), BG)
            d = ImageDraw.Draw(im, "RGBA")
            f_big = font("SemiBold", 34 * U)
            f_body = font("SemiBold", 24 * U) if c["agenda"] else font("Medium", 18 * U)
            step = 44 * U if c["agenda"] else 32 * U
            head = wrap(c["title"], f_big, W - 2 * MARGIN) if c["title"] else []
            items = [wrap(x, f_body, min(W - 2 * MARGIN, 760 * U)) for x in c["body"]]
            nlines = sum(len(x) for x in items)
            block = 48 * U * len(head) + (26 * U if head and items else 0) + step * nlines + 14 * U * (len(items) - 1)
            y = (H - block) / 2 - 20 * U
            for line in head:
                d.text((MARGIN, y), line, font=f_big, fill=FG)
                y += 48 * U
            y += 26 * U if head and items else 0
            for k, lines in enumerate(items):
                col = INK2
                if c["current"] is not None:
                    col = FG if c["body"][k] == c["current"] else MUTED
                for line in lines:
                    d.text((MARGIN, y), line, font=f_body, fill=ink(col, alphas[k]))
                    y += step
                y += 14 * U
            self.chart_cache[key] = im
        return self.chart_cache[key].copy()

    def flow_frame(self, b, t):
        """A row of steps with a bracket under the part that was measured. Steps and the bracket can wait for
        their sentence with at: k."""
        f = b.flow
        steps = [x if isinstance(x, dict) else {"label": x} for x in f["steps"]]
        span = f.get("span")
        vis = lambda item: min(1.0, max(0.0, (t - b.at(item.get("at", 0))) / 0.3)) if b.marks else 1.0
        alphas = tuple(round(vis(x), 2) for x in steps) + ((round(vis(span), 2),) if span else ())
        key = (id(b), alphas)
        if key in self.chart_cache:
            return self.chart_cache[key].copy()
        S, k = 2, 2 * U
        im = Image.new("RGB", (W * S, H * S), BG)
        d = ImageDraw.Draw(im, "RGBA")
        f_title, f_sub, f_step = font("SemiBold", 22 * k), font("Medium", 13 * k), font("Medium", 14 * k)
        x0, y0 = MARGIN * S, MARGIN * S * 0.75
        if f.get("title"):
            d.text((x0, y0), f["title"], font=f_title, fill=FG)
        if f.get("source"):
            d.text((x0, y0 + 32 * k), f["source"], font=f_sub, fill=MUTED)
        n = len(steps)
        gap = 22 * k
        bw = ((W - 2 * MARGIN) * S - gap * (n - 1)) / n
        wrapped = [wrap(x["label"], f_step, bw - 20 * k) for x in steps]
        bh = max(len(w) for w in wrapped) * 20 * k + 28 * k
        by = (H * S) * 0.44 - bh / 2
        for j, (x, lines) in enumerate(zip(steps, wrapped)):
            a = alphas[j]
            if a <= 0:
                continue
            bx = x0 + j * (bw + gap)
            d.rounded_rectangle((bx, by, bx + bw, by + bh), 8 * k, fill=GRID + (int(255 * a),))
            ty = by + (bh - len(lines) * 20 * k) / 2 - 2 * k
            for line in lines:
                d.text((bx + (bw - f_step.getlength(line)) / 2, ty), line, font=f_step, fill=ink(FG, a))
                ty += 20 * k
            if j and alphas[j - 1] > 0:
                d.line((bx - gap + 5 * k, by + bh / 2, bx - 5 * k, by + bh / 2), fill=MUTED + (int(255 * a),), width=k)
        if span and alphas[-1] > 0:
            a = alphas[-1]
            sx0 = x0 + span["from"] * (bw + gap)
            sx1 = x0 + span["to"] * (bw + gap) + bw
            sy = by + bh + 26 * k
            col = ACCENT + (int(255 * a),)
            d.line((sx0, sy, sx1, sy), fill=col, width=2 * k)
            d.line((sx0, sy - 10 * k, sx0, sy), fill=col, width=2 * k)
            d.line((sx1, sy - 10 * k, sx1, sy), fill=col, width=2 * k)
            f_span = font("SemiBold", 16 * k)
            lab = span.get("label", "")
            d.text(((sx0 + sx1) / 2 - f_span.getlength(lab) / 2, sy + 14 * k), lab, font=f_span, fill=ink(FG, a))
        self.chart_cache[key] = im.resize((W, H), Image.LANCZOS)
        return self.chart_cache[key].copy()

    def media_frame(self, b, t):
        m = b.media
        k = min(len(m["frames"]) - 1, max(0, int((t - b.start) * FPS)))
        im = Image.new("RGB", (W, H), BG)
        paste_media(im, m["frames"][k], m["box"], m["rounded"])
        return im

    def scene(self, b, t):
        if b is not None and b.chart:
            return self.chart_frame(b, t)
        if b is not None and b.media:
            return self.media_frame(b, t)
        if b is not None and b.timeline:
            return self.timeline_frame(b, t)
        if b is not None and b.card:
            return self.card_frame(b, t)
        if b is not None and b.flow:
            return self.flow_frame(b, t)
        return self.terminal(t, b)

    def frame(self, t):
        i, b = self.beat_at(t)
        im = self.scene(b, t)
        if i and t - b.start < XFADE and (b.media or b.card or b.flow or self.beats[i - 1].kind != b.kind):
            prev = self.scene(self.beats[i - 1], b.start - 1e-3)  # crossfade between scenes
            im = Image.blend(prev, im, (t - b.start) / XFADE)
        return self.overlays(im, t)


def fit_size(spec, snaps):
    """Crop the rendered terminal to what the recording actually used, so text renders as large as possible."""
    cols, rows = spec.get("size", [100, 22])
    if spec.get("fit", True) is False:
        return cols, rows
    used_r = max(max((y for y, l in enumerate(s.lines) if l.strip()), default=0) for s in snaps)
    used_r = max(used_r, max(s.cursor[1] for s in snaps))
    used_c = max(len(l.rstrip()) for s in snaps for l in s.lines)
    fit = min(cols, max(64, used_c + 16)), min(rows, max(8, used_r + 2))
    log(f"terminal {cols}x{rows} -> fit {fit[0]}x{fit[1]}")
    return fit


def place_callouts(beats, snaps, L, f_label):
    snap_t = [s.t for s in snaps]
    for b in beats:
        c = b.spec.get("callout")
        if not c:
            continue
        for item in c if isinstance(c, list) else [c]:
            co = Callout(item["find"], item.get("label", ""))
            co.on, co.off = b.done + 0.15, b.end
            s = snaps[max(0, bisect.bisect_right(snap_t, b.done + 0.01) - 1)]
            pat = co.find if item.get("regex") else re.escape(co.find)
            hits = [(y, m.start(), m.end()) for y, line in enumerate(s.lines) for m in re.finditer(pat, line)]
            if not hits:
                log(f"callout: {co.find!r} not found on screen after {b.spec.get('run')!r}")
                continue
            y, x0, x1 = hits[item.get("nth", -1)]
            co.cell = (y, x0, x1)
            need = math.ceil(f_label.getlength(co.label) / L.cw) + 2
            cols = len(s.lines[0])

            def free(row, a, z):
                return 0 <= row < len(s.lines) and 0 <= a and z <= cols and not s.lines[row][a:z].strip()

            eol = len(s.lines[y].rstrip()) + 2
            if free(y, x1 + 1, x1 + 2 + need):
                co.place = ("right", y, x1 + 2)
            elif free(y, eol, eol + need):
                co.place = ("right", y, eol)
            elif free(y + 1, x0, x0 + need) and y + 1 != s.cursor[1]:
                co.place = ("below", y + 1, x0)
            elif free(y - 1, x0, x0 + need):
                co.place = ("above", y - 1, x0)
            else:
                co.place = ("caption",)
            b.callouts.append(co)


def render_video(R, beats, total, has_title, has_outro, workdir, audio):
    """Render only frames where something changes, then encode with the concat demuxer."""
    times = {0.0, total}
    for s in R.snaps:
        times.add(round(s.t, 4))
    for b in beats:
        times |= {b.start, b.end}
        for c in b.callouts:
            times |= {c.on, c.off} | {c.on + k / FPS for k in range(int(0.25 * FPS) + 1)}
    for vt, secs in R.skips:
        times |= {vt, vt + 1.8}
    for i, b in enumerate(beats):
        if b.chart:
            times |= {b.start + k / FPS for k in range(int(CHART_DRAW * FPS) + 2)}
            times |= {b.done - 0.05 + k / FPS for k in range(int(0.3 * FPS) + 2)}
        if b.media:
            times |= {b.start + k / FPS for k in range(len(b.media["frames"]) + 1)}
        if b.timeline:
            times |= {b.start + k / FPS for k in range(int(b.timeline["draw"] * FPS) + 2)}
            times |= {b.done - 0.05 + k / FPS for k in range(int(0.45 * FPS) + 2)}
        for m in b.marks:  # reveals keyed to sentences
            times |= {b.start + m + k / FPS for k in range(int(0.3 * FPS) + 2)}
        if i and (b.media or b.card or b.flow or beats[i - 1].kind != b.kind):
            times |= {b.start + k / FPS for k in range(int(XFADE * FPS) + 1)}
    fade = 0.35
    fades = []
    if has_title:
        fades.append((R.t_term0 - fade, R.t_term0, "title"))
    if has_outro:
        fades.append((R.t_term1, R.t_term1 + fade, "outro"))
    for a, z, _ in fades:
        times |= {a + k / FPS for k in range(int(fade * FPS) + 1)}
    t = R.t_term0
    while t < R.t_term1:  # cursor blink
        if not (R.beat_at(t)[1] and R.beat_at(t)[1].kind != "term"):
            times.add(round(t, 4))
        t += 0.3125
    times = sorted(x for x in times if 0 <= x <= total)
    cards = {}
    frames_dir = os.path.join(workdir, "frames")
    shutil.rmtree(frames_dir, ignore_errors=True)
    os.makedirs(frames_dir)
    lines, last_key = [], None
    for k, (a, z) in enumerate(zip(times, times[1:])):
        if z - a < 1e-4:
            continue
        mid = a + 1e-4
        if has_title and mid < R.t_term0 - fade:
            key, mk = ("title",), lambda: cards.setdefault("title", R.card("title"))
        elif has_outro and mid >= R.t_term1 + fade:
            key, mk = ("outro",), lambda: cards.setdefault("outro", R.card("outro"))
        else:
            key = None
            def mk(mid=mid):
                im = R.frame(min(max(mid, R.t_term0), R.t_term1 - 1e-3))
                for fa, fz, kind in fades:
                    if fa <= mid < fz:
                        c = cards.setdefault(kind, R.card(kind))
                        p = (mid - fa) / (fz - fa)
                        im = Image.blend(c, im, p) if kind == "title" else Image.blend(im, c, p)
                return im
        if key is not None and key == last_key:
            lines[-1][1] += z - a
            continue
        path = os.path.join(frames_dir, f"{k:05d}.png")
        mk().save(path, compress_level=1)
        lines.append([path, z - a])
        last_key = key
    concat = os.path.join(workdir, "frames.txt")
    with open(concat, "w") as f:
        f.write("ffconcat version 1.0\n")
        for p, d in lines:
            f.write(f"file '{p}'\nduration {d:.4f}\n")
        f.write(f"file '{lines[-1][0]}'\n")
    out = os.path.join(workdir, "proof.mp4")
    cmd = [FFMPEG, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", concat]
    if audio:
        cmd += ["-i", audio]
    cmd += ["-vf", f"fps={FPS},format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-tune", "animation", "-movflags", "+faststart", "-t", f"{total:.3f}"]
    if audio:
        cmd += ["-c:a", "aac", "-b:a", "128k"]
    subprocess.run(cmd + [out], check=True)
    return out, len(lines)


# ---------------------------------------------------------------- publish / verify

def tailnet_host():
    out = subprocess.run([TAILSCALE, "status", "--json"], capture_output=True, text=True, check=True).stdout
    return json.loads(out)["Self"]["DNSName"].rstrip(".")


def ensure_serving():
    try:
        subprocess.run(["curl", "-fsS", "-o", "/dev/null", "http://127.0.0.1:8740/"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        subprocess.run(["launchctl", "kickstart", "-k", f"gui/{os.getuid()}/dev.captures.serve"], capture_output=True)
        time.sleep(1)
    st = subprocess.run([TAILSCALE, "serve", "status"], capture_output=True, text=True).stdout
    if "/captures" not in st:
        subprocess.run([TAILSCALE, "serve", "--bg", "--set-path", "/captures", "http://127.0.0.1:8740"],
                       check=True, capture_output=True)


def publish(src_dir, slug):
    ensure_serving()
    name = f"{dt.date.today():%Y-%m-%d}-{slug}"
    dest = os.path.join(BUCKET, name)
    shutil.rmtree(dest, ignore_errors=True)
    shutil.copytree(src_dir, dest, ignore=shutil.ignore_patterns("frames", "frames.txt", "*.wav"))
    return f"https://{tailnet_host()}/captures/{urllib.parse.quote(name)}/"


def add_chapters(mp4, chapters, total):
    """Write chapter markers into the mp4 so players show them as a jump list; no re-encode."""
    meta = os.path.join(os.path.dirname(mp4), "chapters.txt")
    with open(meta, "w") as f:
        f.write(";FFMETADATA1\n")
        for k, (name, a) in enumerate(chapters):
            z = chapters[k + 1][1] if k + 1 < len(chapters) else total
            f.write(f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={int(a * 1000)}\nEND={int(z * 1000)}\ntitle={name}\n")
    tmp = mp4 + ".tmp.mp4"
    subprocess.run([FFMPEG, "-v", "error", "-y", "-i", mp4, "-i", meta, "-map", "0", "-map_metadata", "1",
                    "-map_chapters", "1", "-c", "copy", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, mp4)


def probe_duration(path):
    err = subprocess.run([FFMPEG, "-i", path], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err)
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else 0.0


def contact_sheet(mp4, out, dur, n=12):
    step = max(dur / n, 0.1)
    subprocess.run([FFMPEG, "-v", "error", "-y", "-i", mp4, "-vf",
                    f"fps=1/{step:.3f},scale=480:-1,tile=4x{math.ceil(n / 4)}", "-frames:v", "1", out], check=True)


def pr_comment(args, spec, beats, url, dur):
    return f"{url}\n"


def attach(path, repo):
    """Upload to GitHub user-attachments with the gh-attach extension. On a private repo only people with
    access to it can load the URL, so this is how proofs of private work get into PRs."""
    if subprocess.run(["gh", "attach", "--help"], capture_output=True).returncode:
        raise SystemExit("needs the gh-attach extension: gh extension install sudosubin/gh-attach")
    repo = repo or subprocess.run(["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
                                  capture_output=True, text=True).stdout.strip()
    if not repo:
        raise SystemExit("attach: pass --repo owner/name (not inside a GitHub checkout)")
    mb = os.path.getsize(path) / 1e6
    if mb > 100:
        raise SystemExit(f"attach: {mb:.0f} MB is over GitHub's 100 MB video limit")
    if mb > 10:
        log(f"attach: {mb:.0f} MB; GitHub free plans cap videos at 10 MB")
    out = subprocess.run(["gh", "attach", "upload", path, "-R", repo, "--json", "href"],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)[0]["href"]


def post_comment(pr, repo, body):
    q = ["gh", "pr", "view", str(pr), "--json", "author", "-q", ".author.login"] + (["-R", repo] if repo else [])
    author = subprocess.run(q, capture_output=True, text=True).stdout.strip()
    if author != "btn0s":
        raise SystemExit(f"refusing to comment on PR #{pr}: author is {author or 'unknown'}, not btn0s")
    subprocess.run(["gh", "pr", "comment", str(pr), "--body", body] + (["-R", repo] if repo else []), check=True)


# ---------------------------------------------------------------- commands

def find_project_config(start):
    d = os.path.dirname(os.path.abspath(start))
    while True:
        for name in ("proof.config.yaml", ".proof.yaml"):
            if os.path.exists(os.path.join(d, name)):
                return os.path.join(d, name)
        if os.path.exists(os.path.join(d, ".git")) or d == os.path.dirname(d):
            return None
        d = os.path.dirname(d)


def merge_project_config(spec, spec_path):
    """Project defaults (layouts, capture settings, voice, size...) sit under the spec; the spec wins, key by key."""
    path = find_project_config(spec_path)
    if not path:
        return spec
    cfg = yaml.safe_load(open(path)) or {}
    log(f"project config: {path}")
    out = dict(cfg)
    for k, v in spec.items():
        out[k] = {**out[k], **v} if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def cmd_run(a):
    T = {"start": time.time()}
    spec_path = os.path.abspath(a.spec)
    spec = merge_project_config(yaml.safe_load(open(spec_path)), spec_path)
    spec["_path"] = spec_path
    raw = a.raw or spec.get("tier") == 1
    narrate = not (a.no_narrate or spec.get("narrate", True) is False or raw)
    if narrate and not os.path.exists(TTS_PY):
        raise SystemExit(f"proof narrates by default, but Kokoro isn't installed: run "
                         f"{os.path.join(os.path.dirname(HERE), 'install.sh')} (or pass --no-narrate)")
    slug = a.slug or spec.get("slug") or re.sub(r"[^a-z0-9]+", "-", spec.get("title", "proof").lower()).strip("-")[:48]
    workdir = os.path.abspath(a.out or os.path.join(os.path.dirname(spec_path), "proof-out", slug))
    os.makedirs(workdir, exist_ok=True)
    beats = [Beat(s) for s in spec["beats"]]

    spec["_agenda"] = [b.spec["chapter"] for b in beats[1:] if b.spec.get("chapter")]
    durs = {}
    said = {i: b.spec.get("say") or b.spec.get("caption") for i, b in enumerate(beats)
            if b.spec.get("say") or b.spec.get("caption")}
    said = {i: (v if isinstance(v, list) else [v]) for i, v in said.items()}
    if narrate:
        lines = {(i, k): text for i, v in said.items() for k, text in enumerate(v)}
        voiced = synthesize(lines, spec.get("voice", "af_heart"), float(spec.get("speed", 1.05)))
        for i, v in said.items():
            parts = [voiced[(i, k)] for k in range(len(v))]
            if len(parts) == 1:
                beats[i].voice, beats[i].voice_dur = parts[0]
            else:  # one track per beat; marks say where each sentence starts
                beats[i].voice = os.path.join(workdir, f"voice-{i:02d}.wav")
                beats[i].voice_dur = join_wavs([p for p, _ in parts], beats[i].voice, SENTENCE_GAP)
            beats[i].marks = [0.15 + sum(d + SENTENCE_GAP for _, d in parts[:k]) for k in range(len(parts))]
            durs[i] = beats[i].voice_dur
    else:  # silent: pace reveals by reading speed
        for i, v in said.items():
            beats[i].marks = [0.15 + sum(len(x.split()) / 2.8 + SENTENCE_GAP for x in v[:k]) for k in range(len(v))]
            durs[i] = beats[i].marks[-1] + len(v[-1].split()) / 2.8 if len(v) > 1 else 0
    T["tts"] = time.time()

    has_title = bool(spec.get("title_card")) and not raw  # off by default: the PR heading carries the title
    t0 = 1.8 if has_title else 0.0
    snaps, skips, t_end = record_terminal(spec, beats, t0, durs)
    T["record"] = time.time()

    L = Layout(*fit_size(spec, snaps), raw)
    R = Renderer(spec, L, beats, snaps, skips, t0, t_end, raw, has_title)
    place_callouts(beats, snaps, L, R.f_label)
    total = t_end + 0.4
    audio = None
    if narrate:
        audio = os.path.join(workdir, "voice.wav")
        mix_audio(beats, total, audio)
    mp4, nframes = render_video(R, beats, total, has_title, False, workdir, audio)
    last = beats[-1]
    R.frame((last.done + last.end) / 2).save(os.path.join(workdir, "poster.png"))
    T["render"] = time.time()

    chapters = [(b.spec["chapter"], b.start) for b in beats if b.spec.get("chapter")]
    if chapters:
        add_chapters(mp4, chapters, total)
    dur = probe_duration(mp4)
    contact_sheet(mp4, os.path.join(workdir, "contact.png"), dur)
    shutil.copy(spec_path, os.path.join(workdir, "spec.yaml"))
    url = None
    if not a.no_publish:  # only the video goes public; contact sheet, poster, and spec stay in workdir
        stage = tempfile.mkdtemp()
        shutil.copy(mp4, stage)
        url = publish(stage, slug) + os.path.basename(mp4)
    attachment = attach(mp4, a.repo) if a.attach or a.pr else None
    T["publish"] = time.time()

    missing = [c.find for b in beats for c in b.callouts if not c.cell] + [
        (it if isinstance(it, dict) else {}).get("find") for b in beats
        for it in (b.spec.get("callout") if isinstance(b.spec.get("callout"), list) else [b.spec.get("callout")] if b.spec.get("callout") else [])
        if not any(c.find == it["find"] for c in b.callouts)]
    summary = {
        "url": url, "attachment": attachment, "mp4": mp4, "contact_sheet": os.path.join(workdir, "contact.png"),
        "duration_s": round(dur, 2), "frames_rendered": nframes, "narrated": narrate,
        "chapters": [{"title": n, "start": round(a, 2), "at": f"{int(a // 60)}:{int(a % 60):02d}"} for n, a in chapters],
        "beats": [{"caption": b.spec.get("caption"), "start": round(b.start, 2), "end": round(b.end, 2),
                   "sentences_at": [round(b.start + m, 2) for m in b.marks],
                   "callouts": [{"find": c.find, "place": c.place[0]} for c in b.callouts]} for b in beats],
        "callouts_not_found": missing,
        "timing_s": {"tts": round(T["tts"] - T["start"], 1), "record": round(T["record"] - T["tts"], 1),
                     "render+encode": round(T["render"] - T["record"], 1),
                     "verify+publish": round(T["publish"] - T["render"], 1),
                     "total": round(T["publish"] - T["start"], 1)},
    }
    if a.pr:
        body = pr_comment(a, spec, beats, attachment, dur)  # a video URL on its own line plays inline
        with open(os.path.join(workdir, "pr-comment.md"), "w") as f:
            f.write(body)
        summary["pr_comment"] = os.path.join(workdir, "pr-comment.md")
        if a.post:
            post_comment(a.pr, a.repo, body)
            summary["posted"] = True
    print(json.dumps(summary, indent=2))


def cap_target(a):
    return ["--window", str(a.window)] if a.window else ["--screen", str(a.screen or 4)]


def cmd_shot(a):
    slug = a.slug or f"shot-{dt.datetime.now():%H%M%S}"
    workdir = tempfile.mkdtemp()
    subprocess.run([CAP, "screenshot", *cap_target(a), "--path", os.path.join(workdir, "shot.png"), "--json"],
                   check=True, stdout=subprocess.DEVNULL)
    url = publish(workdir, slug)
    print(json.dumps({"url": url + "shot.png", "file": os.path.join(workdir, "shot.png")}, indent=2))


def cmd_clip(a):
    slug = a.slug or f"clip-{dt.datetime.now():%H%M%S}"
    workdir = tempfile.mkdtemp()
    capf, mp4 = os.path.join(workdir, "clip.cap"), os.path.join(workdir, "clip.mp4")
    rec = subprocess.Popen([CAP, "record", "start", *cap_target(a), "--fps", "30", "--duration", str(a.duration),
                            "--path", capf, "--json"], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if a.command:
        time.sleep(1.0)
        subprocess.run(a.command)
    rec.wait()
    subprocess.run([CAP, "export", capf, "-o", mp4, "--fps", "30", "--json"], check=True, stdout=subprocess.DEVNULL)
    shutil.rmtree(capf, ignore_errors=True)
    url = publish(workdir, slug)
    print(json.dumps({"url": url + "clip.mp4", "duration_s": round(probe_duration(mp4), 2)}, indent=2))


def cmd_publish(a):
    src = os.path.abspath(a.path)
    slug = a.slug or re.sub(r"[^a-z0-9]+", "-", os.path.splitext(os.path.basename(src))[0].lower()).strip("-")
    if os.path.isdir(src):
        print(publish(src, slug))
    else:
        d = tempfile.mkdtemp()
        shutil.copy(src, d)
        print(publish(d, slug) + urllib.parse.quote(os.path.basename(src)))


def main():
    ap = argparse.ArgumentParser(prog="proof", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="render a terminal proof from a spec")
    r.add_argument("spec")
    r.add_argument("--no-narrate", action="store_true", help="skip the Kokoro voice (on by default; say: or caption per beat)")
    r.add_argument("--narrate", action="store_true", help=argparse.SUPPRESS)  # old flag, now the default
    r.add_argument("--raw", action="store_true", help="terminal only: no title, captions, or callouts")
    r.add_argument("--no-publish", action="store_true")
    r.add_argument("--slug")
    r.add_argument("--out")
    r.add_argument("--attach", action="store_true", help="also upload as a GitHub attachment (see proof attach)")
    r.add_argument("--pr", type=int, help="attach, and write pr-comment.md for this PR")
    r.add_argument("--repo", help="owner/name for --attach/--pr/--post; defaults to the current checkout")
    r.add_argument("--post", action="store_true", help="post the comment with gh (btn0s PRs only)")
    for name, fn in (("shot", cmd_shot), ("clip", cmd_clip)):
        p = sub.add_parser(name, help=f"{name} the real screen with cap")
        p.add_argument("--screen", type=int)
        p.add_argument("--window", type=int)
        p.add_argument("--slug")
        if name == "clip":
            p.add_argument("--duration", type=int, required=True)
            p.add_argument("command", nargs=argparse.REMAINDER)
        p.set_defaults(fn=fn)
    p = sub.add_parser("publish", help="publish a file or directory to the tailnet bucket")
    p.add_argument("path")
    p.add_argument("--slug")
    p.set_defaults(fn=cmd_publish)
    p = sub.add_parser("attach", help="upload a file as a GitHub attachment and print its URL")
    p.add_argument("path")
    p.add_argument("--repo")
    p.set_defaults(fn=lambda a: print(attach(os.path.abspath(a.path), a.repo)))
    r.set_defaults(fn=cmd_run)
    a = ap.parse_args()
    if getattr(a, "command", None) and a.command[:1] == ["--"]:
        a.command = a.command[1:]
    a.fn(a)


if __name__ == "__main__":
    main()
