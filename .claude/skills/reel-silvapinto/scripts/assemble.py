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
times = [c["t"] - 0.25 for c in tl["cards"] if c["t"] > 0.5] + [tl["outroAt"] - 0.2] + [x["t"] - 0.15 for x in tl.get("inserts", [])]
inputs = ["-i", src]
for i, t in enumerate(times):
    inputs += ["-i", wh]; ms = int(max(t, 0) * 1000)
    parts.append(f"[{i + 2}]adelay={ms}|{ms},volume=0.35[w{i}]")
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
