#!/usr/bin/env python3
"""Build timeline.json for comp_reel.html from a project config.json.

Usage:  python3 build_timeline.py <project_dir>

The project dir must contain:
  config.json   - see references/pipeline.md (section "config.json")
  words.json    - word timestamps from transcribe.py  [{"w","s","e"}, ...]
  sents.json    - sentence timestamps from transcribe.py [{"s","e","t"}, ...]
  src_frames/   - frames extracted by extract_frames.py (f00001.jpg ...)

Time anchors in config.json can be a number (seconds, OUTPUT timeline) or an object
{"word": "anulação", "after": 24, "nth": 0, "offset": -0.1} resolved against the
retimed transcript, so overlays land exactly on the spoken word even after silence cuts.
"""
import json, os, re, sys

FPS = 24
proj = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
cfg = json.load(open(os.path.join(proj, "config.json")))
words = json.load(open(os.path.join(proj, cfg.get("words", "words.json"))))
sents = json.load(open(os.path.join(proj, cfg.get("sents", "sents.json"))))
frames_dir = os.path.join(proj, cfg.get("frames", "src_frames"))
frame_count = len([f for f in os.listdir(frames_dir) if f.endswith(".jpg")])
src_total = frame_count / FPS

# ---------- EDL: cut pauses longer than GAP; keep PRE before speech and POST after ----------
GAP = cfg.get("silence_gap", 0.55); PRE, POST = 0.14, 0.22
segs = []; start = max(0.0, words[0]["s"] - 0.25)
for a, b in zip(words, words[1:]):
    if b["s"] - a["e"] > GAP:
        segs.append([start, a["e"] + POST]); start = b["s"] - PRE
# "tail": seconds kept after the last word (frames beyond the source hold the last frame, audio is padded)
segs.append([start, words[-1]["e"] + cfg.get("tail", 1.2)])
edl = []; acc = 0.0
for s0, s1 in segs:
    d = s1 - s0; edl.append({"src": round(s0, 3), "out": round(acc, 3), "dur": round(d, 3)}); acc += d
out_total = acc

def to_out(ts):
    for e in edl:
        if e["src"] - 1e-6 <= ts <= e["src"] + e["dur"] + 1e-6: return e["out"] + (ts - e["src"])
    for e in edl:
        if ts < e["src"]: return e["out"]
    return out_total

W = [{"w": w["w"], "s": round(to_out(w["s"]), 3), "e": round(to_out(w["e"]), 3)} for w in words]
S = [{"s": round(to_out(s["s"]), 3), "e": round(to_out(s["e"]), 3), "t": s["t"]} for s in sents]
print(f"source {src_total:.1f}s -> output {out_total:.1f}s, {len(segs)} segments, removed {src_total - out_total:.1f}s")

# ---------- caption chunks: 2-3 words, ~22 chars, breaks at punctuation, no lone short words ----------
chunks = []; cur = []
def flush():
    global cur
    if cur: chunks.append({"s": cur[0]["s"], "e": cur[-1]["e"], "words": cur}); cur = []
for i, w in enumerate(W):
    cur.append(w); txt = " ".join(x["w"] for x in cur); nxt = W[i + 1] if i + 1 < len(W) else None
    punct = re.search(r"[.,!?;:]$", w["w"]) is not None
    if len(cur) >= 3 or len(txt) >= 22 or (punct and len(cur) >= 2) or (nxt and nxt["s"] - w["e"] > 0.5): flush()
flush()
merged = []
for c in chunks:
    if merged and len(c["words"]) == 1 and len(c["words"][0]["w"]) <= 3 and len(merged[-1]["words"]) < 4:
        merged[-1]["words"] += c["words"]; merged[-1]["e"] = c["e"]
    else: merged.append(c)
chunks = merged
for i in range(len(chunks) - 1):
    if chunks[i + 1]["s"] - chunks[i]["e"] < 0.6: chunks[i]["e"] = chunks[i + 1]["s"]

# ---------- anchors ----------
def t_of(word, after=0.0, nth=0):
    hits = [w["s"] for w in W if w["s"] >= after and w["w"].lower().strip(".,!?;:") == word.lower()]
    if len(hits) <= nth: raise SystemExit(f"anchor not found: '{word}' after {after}s")
    return hits[nth]

def T(a, default=None):
    if a is None: return default
    if isinstance(a, (int, float)): return float(a)
    if isinstance(a, dict):
        if "word" in a: return round(t_of(a["word"], a.get("after", 0.0), a.get("nth", 0)) + a.get("offset", 0.0), 3)
        if "src" in a: return round(to_out(a["src"]) + a.get("offset", 0.0), 3)
    raise SystemExit(f"bad anchor: {a}")

# ---------- text overlays ("cards"): kinetic gold titles over the live video ----------
cards = []
for c in cfg.get("cards", []):
    cards.append({"t": T(c["at"]), "dur": c.get("dur", 2.1), "kicker": c.get("kicker", ""), "title": c["title"],
                  "size": c.get("size", "small"), "white": c.get("white", False), "sub": c.get("sub")})
cards.sort(key=lambda c: c["t"])
outro_at = min(T(cfg["outro"]["at"]), out_total - 3.6)
intro_end = cfg.get("intro_end")
intro_end = T(intro_end) if intro_end is not None else (cards[1]["t"] + cards[1]["dur"] if len(cards) > 1 and cards[0]["t"] == 0 else 0.0)

# ---------- infographic scenes: each has "from" and "to"; "to" may be "next" or "outro" ----------
raw = cfg.get("scenes", [])
scenes = []
for i, sc in enumerate(raw):
    t0 = T(sc["from"]); to = sc.get("to", "next")
    if to == "next": t1 = T(raw[i + 1]["from"]) if i + 1 < len(raw) else outro_at
    elif to == "outro": t1 = outro_at
    else: t1 = T(to)
    # never overlap a full text overlay: trim to the nearest card edges
    for c in cards:
        if c["t"] > 0 and t0 < c["t"] < t1: t1 = min(t1, c["t"])
        if c["t"] <= t0 < c["t"] + c["dur"]: t0 = c["t"] + c["dur"]
    d = dict(sc); d.pop("from", None); d.pop("to", None)
    if "stagger" in d: d["stagger"] = [T(x) - t0 if isinstance(x, dict) else x for x in d["stagger"]]
    d.update({"t": round(t0, 3), "dur": round(t1 - t0, 3)})
    if d["dur"] > 0.4: scenes.append(d)

# ---------- camera, modeled on the reference edits (see references/estilo.md) ----------
sent_starts = [round(x["s"], 3) for x in S]
edl_cuts = [round(e["out"], 3) for e in edl[1:]]
bounds = [0.0]; last = 0.0
for t in sorted(set(sent_starts + edl_cuts)):
    if t < 1.0 or t > outro_at - 2.0: continue
    forced = any(abs(t - c) < 0.05 for c in edl_cuts)
    if any(k["t"] - 0.6 <= t <= k["t"] + k["dur"] + 0.6 for k in cards) and not forced: continue
    if t - last >= cfg.get("min_shot", 6.5) or forced:
        bounds.append(t); last = t
bounds.append(out_total)
clean = [bounds[0]]
for t in bounds[1:]:
    forced = any(abs(t - c) < 0.05 for c in edl_cuts) or t == out_total
    if t - clean[-1] < 3.5:
        if forced and clean[-1] != 0.0 and not any(abs(clean[-1] - c) < 0.05 for c in edl_cuts): clean[-1] = t
        continue
    clean.append(t)
bounds = clean
levels = cfg.get("framings", [1.0, 1.13, 1.0, 1.26, 1.13, 1.0, 1.26, 1.0, 1.13, 1.26, 1.0, 1.13])
shots = [{"t": bounds[i], "end": bounds[i + 1], "scale": levels[i % len(levels)],
          "drift": 0.06 if levels[i % len(levels)] > 1.0 else 0.035} for i in range(len(bounds) - 1)]
hits = []
for h in cfg.get("hits", []):
    try: t = T(h)
    except SystemExit as e: print("skip hit:", e); continue
    if any(k["t"] - 0.3 <= t <= k["t"] + k["dur"] + 0.3 for k in cards): continue
    hits.append({"t": round(t - 0.05, 3), "dur": cfg.get("hit_dur", 1.1), "scale": cfg.get("hit_scale", 1.2)})
inserts = []
for ins in cfg.get("inserts", []):
    inserts.append({"t": round(T(ins["at"]) - 0.1, 3), "dur": ins.get("dur", 1.3), "img": ins["img"]})

# asset paths: "assets/..." resolves inside the skill's assets folder, anything else inside the project dir
SKILL_ASSETS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
def P(x):
    if not x: return x
    return os.path.join(SKILL_ASSETS, x[len("assets/"):]) if x.startswith("assets/") else os.path.join(proj, x)
brand = dict(cfg.get("brand", {})); brand["mono"] = P(brand.get("mono", "assets/brand/logo_mono.png"))
for ins in inserts: ins["img"] = P(ins["img"])
tl = {"fps": FPS, "frameCount": frame_count, "framePrefix": cfg.get("frames", "src_frames") + "/f", "total": round(out_total, 2),
      "edl": edl, "chunks": chunks, "cards": cards, "scenes": scenes, "shots": shots, "hits": hits, "inserts": inserts,
      "cuts": edl_cuts, "introEnd": round(intro_end, 2), "outroAt": round(outro_at, 2),
      "outFrames": os.path.join(proj, "out_frames"), "brand": brand, "badge": P(cfg.get("badge")), "badgeWidth": cfg.get("badge_width"),
      "source": os.path.join(proj, cfg["video"]), "pivot": cfg.get("pivot")}
json.dump(tl, open(os.path.join(proj, "timeline.json"), "w"), ensure_ascii=False, indent=1)
print("cards", [(round(c["t"], 2), c["title"].replace("<br>", " ")) for c in cards])
print("scenes", [(round(s["t"], 2), round(s["dur"], 2), s["type"]) for s in scenes])
print("shots", [(round(x["t"], 1), x["scale"]) for x in shots], "hits", len(hits), "outro", tl["outroAt"], "total", tl["total"])
