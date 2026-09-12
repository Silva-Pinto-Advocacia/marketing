#!/usr/bin/env python3
"""Transcribe the source video with word timestamps (faster-whisper, CPU).

Usage: python3 transcribe.py <project_dir> [model=medium]
Writes words.json ([{"w","s","e"}]) and sents.json ([{"s","e","t"}]) into the project dir.
The medium model takes ~1 min per minute of audio on 4 CPU cores; "small" is 3x faster and fine for drafts.
"""
import json, os, subprocess, sys, shutil

proj = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
model_name = sys.argv[2] if len(sys.argv) > 2 else "medium"
cfg = json.load(open(os.path.join(proj, "config.json")))
video = os.path.join(proj, cfg["video"])
wav = os.path.join(proj, "audio16k.wav")
ff = shutil.which("ffmpeg")
if not ff:
    import imageio_ffmpeg; ff = imageio_ffmpeg.get_ffmpeg_exe()
subprocess.run([ff, "-y", "-hide_banner", "-loglevel", "error", "-i", video, "-vn", "-ac", "1", "-ar", "16000", wav], check=True)

from faster_whisper import WhisperModel
m = WhisperModel(model_name, device="cpu", compute_type="int8")
segs, _ = m.transcribe(wav, language=cfg.get("language", "pt"), word_timestamps=True, vad_filter=True, beam_size=5)
words, sents = [], []
for s in segs:
    sents.append({"s": round(s.start, 2), "e": round(s.end, 2), "t": s.text.strip()})
    for w in s.words:
        words.append({"w": w.word.strip(), "s": round(float(w.start), 2), "e": round(float(w.end), 2)})
json.dump(words, open(os.path.join(proj, "words.json"), "w"), ensure_ascii=False)
json.dump(sents, open(os.path.join(proj, "sents.json"), "w"), ensure_ascii=False, indent=1)
print(f"{len(words)} words, {len(sents)} sentences")
for s in sents: print(f"[{s['s']:6.2f}-{s['e']:6.2f}] {s['t']}")
