#!/usr/bin/env python3
"""Extract the source video as a 24 fps JPEG sequence (1080x1920), optionally cleaning burned-in
elements and reframing. Everything downstream (render, timeline) works on this sequence.

Usage: python3 extract_frames.py <project_dir>

config.json keys used:
  video            source file
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
bb = cfg.get("bottom_blur")
if bb:
    vf += (f",split[g][h];[h]crop=1080:{bb['h']}:0:{bb['y']},gblur=sigma={bb.get('sigma', 20)},format=rgba,"
           f"geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='clip(Y*255/{bb.get('feather', 110)},0,255)'[i];[g][i]overlay=0:{bb['y']}")
crop = cfg.get("crop")
if crop:
    vf += f",crop={crop['w']}:{crop['h']}:{crop['x']}:{crop['y']},scale=1080:1920:flags=lanczos,unsharp=5:5:{cfg.get('sharpen', 0.6)}:5:5:0.0"
else:
    vf += ",scale=1080:1920:flags=lanczos"
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
