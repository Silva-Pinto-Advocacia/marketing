#!/usr/bin/env python3
"""Recorta a pessoa do fundo nos primeiros segundos do video (visual "dinamico").

Usage: python3 recortar.py <project_dir> [segundos]

Gera cut_frames/c00001.png ... (RGBA, a pessoa com fundo transparente) para os quadros da abertura,
que o comp_reel.html poe POR CIMA do texto gigante da abertura: o texto passa por tras da cabeca.
Usa o rembg (modelo u2net_human_seg, ~1 s por quadro em CPU). Sem o rembg, avisa e sai sem erro:
o build_timeline ve que nao ha recorte e a abertura fica sem o texto por tras.
"""
import json, os, sys, time

proj = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
seg = float(sys.argv[2]) if len(sys.argv) > 2 else 3.4
cfg = json.load(open(os.path.join(proj, "config.json")))
words = json.load(open(os.path.join(proj, cfg.get("words", "words.json"))))
frames = os.path.join(proj, cfg.get("frames", "src_frames"))
out = os.path.join(proj, "cut_frames"); os.makedirs(out, exist_ok=True)
try:
    from rembg import remove, new_session
    from PIL import Image
except ImportError:
    print("recortar: rembg indisponivel (pip install rembg onnxruntime); a abertura fica sem o texto por tras")
    sys.exit(0)
FPS = 24
# o primeiro trecho da EDL comeca 0,25 s antes da primeira palavra (ver build_timeline.py)
i0 = max(1, int(max(0.0, words[0]["s"] - 0.25) * FPS) + 1)
n = len([f for f in os.listdir(frames) if f.endswith(".jpg")])
i1 = min(n, i0 + int(seg * FPS) + 2)
sess = new_session("u2net_human_seg"); t0 = time.time()
for i in range(i0, i1 + 1):
    o = os.path.join(out, f"c{i:05d}.png")
    if os.path.exists(o): continue
    im = Image.open(os.path.join(frames, f"f{i:05d}.jpg")).convert("RGB")
    remove(im, session=sess, post_process_mask=True).save(o)
print(f"recortar: quadros {i0} a {i1} em {time.time() - t0:.0f}s")
