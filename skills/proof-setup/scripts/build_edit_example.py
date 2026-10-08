#!/usr/bin/env python3
"""Build the pipeline-demo edit: media timeline (document JSON) + graphics (action batch)."""
import json, sys

W = sys.argv[1]  # .tesseract-work dir
BG = [16/255, 17/255, 24/255, 1]
AMBER = [1.0, 0.72, 0.28, 1]
INK = [0.06, 0.07, 0.09, 1]
WHITE = [0.95, 0.96, 0.98, 1]
GRAY = [0.62, 0.66, 0.74, 1]
CHIP = [0.13, 0.14, 0.19, 0.96]
RED = [0.95, 0.30, 0.30, 1]
BOLD, SEMI, MED = ("Inter", "Bold"), ("Inter", "SemiBold"), ("Inter", "Medium")
DUR = 52000

# --- source-frame geometry of the terminal (22pt Menlo) ---
CW, X0, ROW0, RH = 13.0, 5.0, 78.0, 27.0
AX, AY, PX, PY = 0.0, 78.0, 70.0, 110.0   # framing: source (0,78) -> canvas (70,110)

def to_canvas(sx, sy, s):
    return PX + (sx - AX) * s, PY + (sy - AY) * s

def span_box(row0, row1, col0, col1, s, pad=8):
    x0, y0 = to_canvas(X0 + CW * col0 - pad, ROW0 + RH * row0, s)
    x1, y1 = to_canvas(X0 + CW * col1 + pad, ROW0 + RH * (row1 + 1), s)
    return x0, y0, x1 - x0, y1 - y0

def tf(x=0, y=0, scale=100, opacity=100, anchor=(0, 0)):
    return {"anchorPoint": list(anchor), "position": [x, y], "scale": [scale, scale], "rotation": 0, "opacity": opacity}

# ---------------- media timeline (document JSON) ----------------
doc = json.load(open(f"{W}/editable.base.json"))
doc["dimensions"] = {"width": 1920, "height": 1080}
doc["duration"] = DUR / 1000

SRC_DUR = 61033
segments = [  # id, name, src_start, src_end, edit_start, scale
    (10, "A · record status + targets", 2100, 16300, 6100, 1.50),
    (11, "B1 · cat script", 16400, 21900, 20300, 1.40),
    (12, "B2 · narrate typed", 21950, 24700, 25800, 1.12),
    (13, "C1 · first voice line", 28800, 31800, 28550, 1.12),
    (14, "C2 · last voice lines", 46600, 47800, 31550, 1.12),
    (16, "D1 · tsrct create + import", 48600, 55000, 34600, 1.10),
    (17, "D2 · tsrct import output", 58200, 60950, 41000, 1.10),
]
stills = [(15, "F1 · freeze narrate", "freeze-narrate2", 32750, 34600, 1.12),
          (18, "F2 · freeze tsrct", "freeze-final", 43750, 46300, 1.10)]
layers = []
for lid, name, s0, s1, e0, s in segments:
    layers.append({"type": "Video", "id": lid, "name": name,
                   "activeRange": {"start": e0, "duration": s1 - s0},
                   "sourceRange": {"start": s0, "duration": s1 - s0},
                   "sourceIntrinsicDuration": SRC_DUR,
                   "transform": tf(PX, PY, s * 100, anchor=(AX, AY)),
                   "source": {"assetId": "take", "fit": "contain"}})
for lid, name, asset, e0, e1, s in stills:
    layers.append({"type": "Image", "id": lid, "name": name,
                   "activeRange": {"start": e0, "duration": e1 - e0},
                   "transform": tf(PX, PY, s * 100, anchor=(AX, AY)),
                   "source": {"assetId": asset, "fit": "contain"}})

beats = json.load(open(f"{W}/../audio/manifest.json"))["beats"]
vo_starts = [500, 6900, 14700, 20700, 25900, 35300, 46700]
for i, (b, t) in enumerate(zip(beats, vo_starts), 1):
    d = int(b["duration"] * 1000) - 5
    layers.append({"type": "Audio", "id": 60 + i, "name": f"VO beat {i}",
                   "activeRange": {"start": t, "duration": d}, "sourceRange": {"start": 0, "duration": d},
                   "sourceIntrinsicDuration": int(b["duration"] * 1000), "source": {"assetId": f"vo-{i}"},
                   "volume": 1.0, "captionsEnabled": False})
sfx = [("sfx-whoosh", 600, 0.40, [5950, 45750]), ("sfx-tap", 180, 0.30, [9150, 15750, 21350, 32050, 41250, 43800])]
nid = 80
for asset, d, vol, times in sfx:
    for t in times:
        layers.append({"type": "Audio", "id": nid, "name": f"SFX {asset[4:]} @{t/1000:.2f}s",
                       "activeRange": {"start": t, "duration": d}, "sourceRange": {"start": 0, "duration": d},
                       "sourceIntrinsicDuration": d, "source": {"assetId": asset},
                       "volume": vol, "captionsEnabled": False})
        nid += 1
doc["composition"]["layers"] = layers
json.dump(doc, open(f"{W}/editable.edit.json", "w"), indent=1)

# ---------------- graphics (action batch) ----------------
A = []
_id = [100]
def new_id():
    _id[0] += 1
    return _id[0]

def rect(lid, name, x, y, w, h, fill, start, dur, parent=None, round_=0, stroke=None, front=True):
    r = {"size": [w, h], "fillColor": fill, "roundness": round_}
    if stroke:
        r.update(strokeEnabled=True, strokeColor=stroke[0], strokeWidth=stroke[1])
    a = {"type": "createFxRectLayer", "compositionId": "main", "layerId": lid, "name": name,
         "activeRange": {"start": start, "duration": dur}, "transform": tf(x, y), "rect": r}
    if front: a["insertIndex"] = 0
    if parent: a["parentLayerId"] = parent
    A.append(a)

def text(lid, name, s, font, size, color, x, y, w, h, start, dur, parent=None, just="left", tracking=None):
    st = {"text": s, "fontFamily": font[0], "fontStyle": font[1], "fontSize": size, "fillColor": color,
          "strokeWidth": 0, "justification": just, "boxText": True, "boxPosition": [0, 0], "boxSize": [w, h]}
    if tracking is not None: st["tracking"] = tracking
    a = {"type": "createFxTextLayer", "compositionId": "main", "layerId": lid, "name": name, "insertIndex": 0,
         "activeRange": {"start": start, "duration": dur}, "transform": tf(x, y), "sourceText": st}
    if parent: a["parentLayerId"] = parent
    A.append(a)

def group(lid, name, start, dur):
    A.append({"type": "createFxGroupLayer", "compositionId": "main", "layerId": lid, "name": name,
              "insertIndex": 0, "activeRange": {"start": start, "duration": dur}, "transform": tf()})

def fade(lid, dur, fin=180, fout=180, tag=None, delay=0):
    tag = tag or f"L{lid}"
    ease = {"type": "cubicBezier", "x1": 0.2, "y1": 0, "x2": 0.2, "y2": 1}
    keys = [{"id": f"{tag}-o0", "layerTime": delay, "value": {"type": "float", "value": 0}, "easing": {"type": "linear"}},
            {"id": f"{tag}-o1", "layerTime": delay + fin, "value": {"type": "float", "value": 100}, "easing": ease}]
    if fout:
        keys += [{"id": f"{tag}-o2", "layerTime": dur - fout, "value": {"type": "float", "value": 100}, "easing": {"type": "linear"}},
                 {"id": f"{tag}-o3", "layerTime": dur, "value": {"type": "float", "value": 0}, "easing": {"type": "linear"}}]
    A.append({"type": "setFxPropertyKeyframes", "compositionId": "main",
              "property": {"layerId": lid, "propertyType": "opacity"}, "keyframes": keys})

def chip_w(s, size):
    return int(len(s) * size * 0.54 + 44)

# background + top matte (hide menu bar / title bar above the terminal text)
rect(100, "Background", 0, 0, 1920, 1080, BG, 0, DUR, front=False)
rect(new_id(), "Top matte", 0, 0, 1920, 113, BG, 0, DUR)
rect(new_id(), "Left matte", 0, 0, 75, 1080, BG, 0, DUR)

# live-capture tag in the top matte
g = new_id(); group(g, "Live capture tag", 6100, 40200)
rect(new_id(), "Rec dot", 80, 38, 16, 16, RED, 0, 40200, parent=g, round_=8)
text(new_id(), "Rec label", "LIVE CAPTURE  ·  devbox, headless macOS", SEMI, 22, GRAY, 108, 32, 900, 34, 0, 40200, parent=g, tracking=60)
fade(g, 40200, 300, 250)

# step chips (bottom left)
steps = [("01", "Record", "cap record  ·  cap targets", 6400, 13900),
         ("02", "Narrate", "Kokoro-82M via mlx-audio", 20300, 14300),
         ("03", "Annotate & edit", "Tesseract (tsrct)", 34600, 11700)]
for num, title, sub, t0, d in steps:
    g = new_id(); group(g, f"Step {num} chip", t0, d)
    w = max(chip_w(title, 40), chip_w(sub, 24)) + 90
    rect(new_id(), "Chip bg", 80, 818, w, 112, CHIP, 0, d, parent=g, round_=16)
    rect(new_id(), "Chip accent", 80, 818, 6, 112, AMBER, 0, d, parent=g)
    text(new_id(), "Step number", num, BOLD, 40, AMBER, 108, 834, 70, 50, 0, d, parent=g)
    text(new_id(), "Step title", title, SEMI, 40, WHITE, 176, 834, w - 110, 50, 0, d, parent=g)
    text(new_id(), "Step tool", sub, MED, 24, GRAY, 176, 886, w - 110, 32, 0, d, parent=g)
    fade(g, d, 250, 200)

# callouts: highlight box + amber label chip
def callout(name, box, label, t0, d, where="below"):
    x, y, w, h = box
    g = new_id(); group(g, f"Callout · {name}", t0, d)
    rect(new_id(), "Highlight", x, y, w, h, [AMBER[0], AMBER[1], AMBER[2], 0.10], 0, d, parent=g, round_=8, stroke=(AMBER, 3))
    lw = chip_w(label, 24)
    if where == "inline":  # compact tag sitting inside the row band
        th = int(h) - 2
        lw = chip_w(label, 22) - 8
        lx, ly = x + w + 14, y + 1
        rect(new_id(), "Label bg", lx, ly, lw, th, AMBER, 0, d, parent=g, round_=6)
        text(new_id(), "Label", label, SEMI, 22, INK, lx + 14, ly + (th - 28) / 2, lw - 20, 30, 0, d, parent=g)
        fade(g, d)
        return
    if where == "below":  # sits in the (empty) row just under the highlight
        lx, ly = x, y + h + 4
    else:  # right
        lx, ly = x + w + 18, y + h / 2 - 18
    rect(new_id(), "Label bg", lx, ly, lw, 36, AMBER, 0, d, parent=g, round_=8)
    text(new_id(), "Label", label, SEMI, 24, INK, lx + 18, ly + 3, lw - 24, 32, 0, d, parent=g)
    fade(g, d)

callout("recording", span_box(1, 1, 14, 25, 1.5), "Detached Cap session — recording this screen", 9200, 5100)
callout("display", span_box(8, 8, 2, 17, 1.5), "The display being captured", 15800, 4400, where="right")
callout("script", span_box(1, 7, 0, 95, 1.4), "script.txt — one line per beat", 21400, 4300)
callout("timings", span_box(1, 7, 0, 26, 1.12), "Start + duration per beat → audio/manifest.json", 32100, 2450)
callout("video", span_box(3, 3, 0, 86, 1.1), "Footage packed into the project", 41300, 4950, where="inline")
callout("voice", span_box(5, 5, 0, 55, 1.1), "Voice line → audio asset", 43850, 2400, where="inline")

# jump-cut tag (top right, in the matte)
g = new_id(); group(g, "Jump-cut tag", 31550, 2400)
lab = "»  15 s of speech synthesis skipped"
lw = chip_w(lab, 24)
rect(new_id(), "Tag bg", 1840 - lw, 28, lw, 44, CHIP, 0, 2400, parent=g, round_=10)
text(new_id(), "Tag", lab, SEMI, 24, AMBER, 1840 - lw + 22, 36, lw - 30, 34, 0, 2400, parent=g)
fade(g, 2400, 150, 200)

# captions from the approved narration script
for i, (b, t) in enumerate(zip(beats, vo_starts), 1):
    if i in (1, 7):
        continue  # title and outro cards carry these lines on screen
    d = int(b["duration"] * 1000)
    c = new_id()
    text(c, f"Caption {i}", b["text"], MED, 32, [0.92, 0.93, 0.96, 1], 660, 830, 1180, 100, t, d, just="right")
    fade(c, d, 120, 120)

# title card
g = new_id(); group(g, "Title card", 0, 6400)
rect(new_id(), "Title bg", 0, 0, 1920, 1080, BG, 0, 6400, parent=g)
o = new_id(); text(o, "Overline", "HEADLESS SCREEN CAPTURE", SEMI, 28, AMBER, 0, 372, 1920, 40, 0, 6400, parent=g, just="center", tracking=300)
t = new_id(); text(t, "Title", "Record. Narrate. Annotate.", BOLD, 112, WHITE, 0, 420, 1920, 150, 0, 6400, parent=g, just="center", tracking=-20)
s = new_id(); text(s, "Tools", "cap   ·   Kokoro via mlx-audio   ·   Tesseract", MED, 40, GRAY, 0, 596, 1920, 60, 0, 6400, parent=g, just="center")
fade(o, 6400, 400, 0, delay=200); fade(t, 6400, 500, 0, delay=450); fade(s, 6400, 500, 0, delay=900)
A.append({"type": "setFxPropertyKeyframes", "compositionId": "main", "property": {"layerId": g, "propertyType": "opacity"},
          "keyframes": [{"id": "title-hold", "layerTime": 6000, "value": {"type": "float", "value": 100}, "easing": {"type": "linear"}},
                        {"id": "title-out", "layerTime": 6400, "value": {"type": "float", "value": 0}, "easing": {"type": "linear"}}]})

# outro card
d = DUR - 46000
g = new_id(); group(g, "Outro card", 46000, d)
rect(new_id(), "Outro bg", 0, 0, 1920, 1080, BG, 0, d, parent=g)
text(new_id(), "Outro title", "Record. Narrate. Annotate.", BOLD, 104, WHITE, 0, 400, 1920, 140, 0, d, parent=g, just="center", tracking=-20)
s = new_id(); text(s, "Outro line", "All from the command line, on a headless Mac.", MED, 40, GRAY, 0, 566, 1920, 60, 0, d, parent=g, just="center")
k = new_id(); text(k, "Outro skill", "/screen-capture", SEMI, 34, AMBER, 0, 680, 1920, 50, 0, d, parent=g, just="center")
fade(g, d, 400, 500); fade(s, d, 400, 0, delay=500); fade(k, d, 400, 0, delay=900)

json.dump(A, open(f"{W}/edits.json", "w"), indent=1)
print(f"{len(layers)} media layers, {len(A)} actions")
