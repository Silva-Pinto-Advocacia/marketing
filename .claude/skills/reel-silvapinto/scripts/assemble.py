#!/usr/bin/env python3
"""Mux rendered frames with the source audio cut per EDL, plus whoosh SFX at overlay starts.

Usage: python3 assemble.py <project_dir> [output_name.mp4]
Produces <name>.mp4 (CRF 18 master) and <name>_web.mp4 (CRF 24, under ~30 MB for chat delivery).
"""
import json, os, subprocess, sys, shutil

def ffmpeg_bin():
    for c in (shutil.which("ffmpeg"),):
        if c: return c
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()

FF = ffmpeg_bin()
proj = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
tl = json.load(open(os.path.join(proj, "timeline.json")))
out = os.path.join(proj, sys.argv[2] if len(sys.argv) > 2 else "reel.mp4")
src = tl["source"]

wh = os.path.join(proj, "whoosh.wav")
subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "anoisesrc=d=0.7:c=pink:a=0.6:r=48000",
                "-af", "highpass=f=250,lowpass=f=2600,afade=t=in:d=0.28:curve=esin,afade=t=out:st=0.3:d=0.4,volume=0.9,aformat=channel_layouts=stereo", wh], check=True)

parts = []
for i, e in enumerate(tl["edl"]):
    parts.append(f"[1:a]atrim=start={e['src']}:end={e['src'] + e['dur']},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={max(0, e['dur'] - 0.012)}:d=0.012[s{i}]")
n = len(tl["edl"])
parts.append("".join(f"[s{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1,aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-15:TP=-1.5:LRA=11,aresample=48000[voice]")
# efeitos: no formal, o whoosh antes de cada texto grande, do insert e do encerramento; os eventos de
# timeline["sfx"] (cenas prova e ranking; no dinamico, tudo) vem com o tipo de som de cada um
SFX = {
    "pop": "sine=f=520:d=0.12:r=48000,afade=t=out:st=0.02:d=0.1,asetrate=48000*1.6,aresample=48000,volume=0.8",
    "tick": "anoisesrc=d=0.05:c=white:a=0.9:r=48000,highpass=f=2500,afade=t=out:st=0.005:d=0.045,volume=0.7",
    "boom": "sine=f=58:d=0.7:r=48000,afade=t=out:st=0.03:d=0.65,volume=2.2",
    "scratch": "anoisesrc=d=0.45:c=brown:a=0.9:r=48000,highpass=f=900,lowpass=f=5000,tremolo=f=18:d=0.8,afade=t=in:d=0.04,afade=t=out:st=0.3:d=0.15,volume=1.4",
}
VOL = {"whoosh": 0.35, "pop": 0.3, "tick": 0.25, "boom": 0.45, "scratch": 0.35}
arq = {"whoosh": wh}
for k, f in SFX.items():
    arq[k] = os.path.join(proj, f"sfx_{k}.wav")
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", f, "-ac", "2", arq[k]], check=True)
eventos = [] if tl.get("visual") == "dinamico" else (
    [("whoosh", c["t"] - 0.25) for c in tl["cards"] if c["t"] > 0.5] + [("whoosh", tl["outroAt"] - 0.2)]
    + [("whoosh", x["t"] - 0.15) for x in tl.get("inserts", [])])
eventos += [(e["k"], e["t"]) for e in tl.get("sfx", []) if e["k"] in arq]
times = [t for _, t in eventos]
inputs = ["-i", src]
for i, (k, t) in enumerate(eventos):
    inputs += ["-i", arq[k]]; ms = int(max(t, 0) * 1000)
    parts.append(f"[{i + 2}]adelay={ms}|{ms},volume={VOL[k]}[w{i}]")
parts.append("[voice]" + "".join(f"[w{i}]" for i in range(len(times))) + f"amix=inputs={len(times) + 1}:normalize=0:duration=first,alimiter=limit=0.95,aresample=48000,apad[out]")
fc = ";".join(parts)
subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error",
                "-framerate", str(tl["fps"]), "-i", os.path.join(tl["outFrames"], "o%05d.jpg"), *inputs,
                "-filter_complex", fc, "-map", "0:v", "-map", "[out]",
                "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(tl["fps"]),
                "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
web = out.replace(".mp4", "_web.mp4")
subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", out, "-c:v", "libx264", "-preset", "slow", "-crf", "24", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", web], check=True)
print("master MB", round(os.path.getsize(out) / 1e6, 1), "| web MB", round(os.path.getsize(web) / 1e6, 1))
