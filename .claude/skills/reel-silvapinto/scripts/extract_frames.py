#!/usr/bin/env python3
"""Extract the source video as a 24 fps JPEG sequence (1080x1920, or 1920x1080 with "formato": "deitado"),
optionally cleaning burned-in
elements and reframing. Everything downstream (render, timeline) works on this sequence.

Usage: python3 extract_frames.py <project_dir>

config.json keys used:
  video            source file
  formato          "em_pe" (default, 1080x1920, Reels/Stories) or "deitado" (1920x1080)
  crop             optional {"w":939,"h":1670,"x":70,"y":0} in source pixels, scaled to 1080x1920 (open reframe = ~1.15x)
  delogo           optional list of {"x","y","w","h"} boxes to interpolate away (burned-in logos, captions)
  blur_patches     optional list of {"x","y","w","h","sigma"} boxes blurred after delogo (hides interpolation streaks on flat walls)
  bottom_blur      optional {"y":1280,"h":400,"sigma":20,"feather":110}: progressive blur of the lower band (depth-of-field look)
  sharpen          optional float 0.4-0.7 (unsharp amount after upscaling), default 0.6 when crop is set
  frame_replace    optional list of {"from":1,"to":140,"source_start":439} (frame numbers at 24 fps)

Raw footage (no burned-in elements): set only "video"; leave the rest out.
"""
import json, os, subprocess, sys, shutil

proj = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
cfg = json.load(open(os.path.join(proj, "config.json")))
ff = shutil.which("ffmpeg")
if not ff:
    import imageio_ffmpeg; ff = imageio_ffmpeg.get_ffmpeg_exe()
video = os.path.join(proj, cfg["video"])
out_dir = os.path.join(proj, cfg.get("frames", "src_frames"))
W, H = (1920, 1080) if cfg.get("formato") == "deitado" else (1080, 1920)
if os.path.isdir(out_dir): shutil.rmtree(out_dir)
os.makedirs(out_dir)

chain = ["fps=24"]
for d in cfg.get("delogo", []):
    chain.append(f"delogo=x={d['x']}:y={d['y']}:w={d['w']}:h={d['h']}")
vf = ",".join(chain)
k = 0
for b in cfg.get("blur_patches", []):
    vf += f",split[a{k}][b{k}];[b{k}]crop={b['w']}:{b['h']}:{b['x']}:{b['y']},gblur=sigma={b.get('sigma', 14)}[c{k}];[a{k}][c{k}]overlay={b['x']}:{b['y']}"
    k += 1


def queixo(video, n=8):
    """O queixo mais baixo (px do video de origem) em n quadros, como o build_timeline mede: y + 1,15 h da caixa
    do rosto. None sem OpenCV ou sem rosto."""
    try:
        import cv2
    except ImportError:
        return None
    casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    cap = cv2.VideoCapture(video); total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0); bases = []
    for i in range(n):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(total * (i + 0.5) / n))
        ok, img = cap.read()
        if not ok: continue
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        fs = casc.detectMultiScale(g, 1.1, 6, minSize=(g.shape[1] // 9, g.shape[1] // 9))
        if len(fs):
            x, y, w, h = max(fs, key=lambda f: f[2] * f[3]); bases.append((int(y + 1.15 * h), g.shape[0]))
    cap.release()
    return max(bases) if len(bases) >= 3 else None


bb = cfg.get("bottom_blur")
crop = cfg.get("crop")
# o desfoque da faixa de baixo nunca pega o rosto. Selfie de perto (13/10/2026): o queixo ia ate ~1400 px e o
# desfoque comecava em 1280, borrando a boca. A faixa desce para baixo do queixo; sem espaco, sai
if bb and not crop:
    q = queixo(video)
    if q and q[0] + 20 > bb["y"]:
        bb = dict(bb, y=q[0] + 20)
        bb["h"] = min(bb["h"], q[1] - bb["y"])
        if bb["h"] < bb.get("feather", 110) + 40:
            print(f"desfoque de baixo: saiu (o queixo vai ate {q[0]} px)"); bb = None
        else:
            print(f"desfoque de baixo: desceu para {bb['y']} px (o queixo vai ate {q[0]} px)")
if bb:
    vf += (f",split[g][h];[h]crop=iw:{bb['h']}:0:{bb['y']},gblur=sigma={bb.get('sigma', 20)},format=rgba,"
           f"geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='clip(Y*255/{bb.get('feather', 110)},0,255)'[i];[g][i]overlay=0:{bb['y']}")
if crop:
    vf += f",crop={crop['w']}:{crop['h']}:{crop['x']}:{crop['y']},scale={W}:{H}:flags=lanczos,unsharp=5:5:{cfg.get('sharpen', 0.6)}:5:5:0.0"
else:
    vf += f",scale={W}:{H}:flags=lanczos"
cmd = [ff, "-y", "-hide_banner", "-loglevel", "error", "-i", video, "-vf", vf, "-q:v", "3", os.path.join(out_dir, "f%05d.jpg")]
print("filter:", vf)
subprocess.run(cmd, check=True)
# optional: replace a range of frames with frames from elsewhere in the take (e.g. an intro that has a
# burned-in card over the torso: show a clean stretch of the same take while the intro audio plays)
for r in cfg.get("frame_replace", []):
    for i in range(r["from"], r["to"] + 1):
        j = r["source_start"] + (i - r["from"])
        shutil.copyfile(os.path.join(out_dir, f"f{j:05d}.jpg"), os.path.join(out_dir, f"f{i:05d}.jpg"))
    print(f"replaced frames {r['from']}-{r['to']} with {r['source_start']}+")
print("frames:", len(os.listdir(out_dir)))
