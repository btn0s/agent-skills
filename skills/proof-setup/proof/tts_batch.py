"""Synthesize many lines with one Kokoro model load. Runs inside the mlx-audio tool env.

usage: python tts_batch.py jobs.json   (jobs: [{"text", "out", "voice", "speed", "lang"}])
"""
import json, sys

import numpy as np
from mlx_audio.audio_io import write as audio_write
from mlx_audio.tts.utils import load_model

jobs = json.load(open(sys.argv[1]))
model = load_model(model_path="mlx-community/Kokoro-82M-bf16")
for j in jobs:
    chunks = [np.array(r.audio) for r in model.generate(
        text=j["text"], voice=j["voice"], speed=j["speed"], lang_code=j["lang"], verbose=False)]
    audio_write(j["out"], np.concatenate(chunks), model.sample_rate, format="wav")
    print(j["out"], flush=True)
