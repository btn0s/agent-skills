#!/usr/bin/env python3
"""Turn a beat-per-line narration script into Kokoro WAVs plus a timing manifest.

Usage: narrate.py SCRIPT OUTDIR [--voice af_heart] [--speed 1.0] [--lang a]

Script lines: "[mm:ss.s |] text". Indented lines continue the previous beat.
Blank lines and lines starting with # are ignored.
"""
import argparse, json, os, re, shutil, subprocess, sys, wave

MODEL = "mlx-community/Kokoro-82M-bf16"
TS = re.compile(r"^\s*(?:(\d+):)?(\d+(?:\.\d+)?)\s*\|\s*(.*)$")


def parse(path):
    beats = []
    for raw in open(path, encoding="utf-8"):
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[:1].isspace() and beats and not TS.match(line):
            beats[-1]["text"] += " " + line.strip()
            continue
        m = TS.match(line)
        if m:
            start = int(m.group(1) or 0) * 60 + float(m.group(2))
            beats.append({"start": start, "text": m.group(3).strip()})
        else:
            beats.append({"start": None, "text": line.strip()})
    return beats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("outdir")
    ap.add_argument("--voice", default="af_heart")
    ap.add_argument("--speed", default="1.0")
    ap.add_argument("--lang", default="a", help="a=American, b=British")
    ap.add_argument("--gap", type=float, default=0.3, help="gap for untimed beats (s)")
    a = ap.parse_args()

    exe = shutil.which("mlx_audio.tts.generate") or os.path.expanduser(
        "~/.local/bin/mlx_audio.tts.generate")
    os.makedirs(a.outdir, exist_ok=True)
    beats = parse(a.script)
    if not beats:
        sys.exit("no beats in script")

    cursor = 0.0
    for i, b in enumerate(beats, 1):
        prefix = f"beat-{i:02d}"
        subprocess.run([exe, "--model", MODEL, "--voice", a.voice, "--lang_code", a.lang,
                        "--speed", str(a.speed), "--text", b["text"], "--output_path", a.outdir,
                        "--file_prefix", prefix, "--join_audio"],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        path = os.path.join(a.outdir, prefix + ".wav")
        with wave.open(path) as w:
            dur = w.getnframes() / w.getframerate()
        if b["start"] is None:
            b["start"] = round(cursor, 3)
        b.update(file=os.path.abspath(path), duration=round(dur, 3), end=round(b["start"] + dur, 3))
        cursor = b["end"] + a.gap
        print(f"{prefix}  {b['start']:7.2f}s  +{dur:5.2f}s  {b['text']}")

    for prev, nxt in zip(beats, beats[1:]):
        if prev["end"] > nxt["start"]:
            print(f"warning: beat ending {prev['end']:.2f}s overlaps next start {nxt['start']:.2f}s",
                  file=sys.stderr)

    with open(os.path.join(a.outdir, "manifest.json"), "w") as f:
        json.dump({"voice": a.voice, "speed": float(a.speed), "model": MODEL, "beats": beats}, f, indent=2)


if __name__ == "__main__":
    main()
