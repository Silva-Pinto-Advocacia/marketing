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
# formato: "em_pe" (padrao, 1080x1920, Reels e Stories) ou "deitado" (1920x1080). Deitado, o rosto fica no
# centro e os textos grandes, os infograficos e o brasao da abertura vao para o painel da direita.
DEITADO = cfg.get("formato") == "deitado"
VW, VH = (1920, 1080) if DEITADO else (1080, 1920)
AREA = "painel da direita vazio" if DEITADO else "metade inferior vazia"
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
# gratuidade nunca escrita na tela (Provimento 205/2021): "gratuita", "de graça", "sem custo" saem da legenda;
# o audio fica como foi falado. "legenda_gratuidade": true desliga o filtro
if not cfg.get("legenda_gratuidade"):
    nrm = lambda x: x.lower().strip(".,!?;:")
    for c in chunks:
        ws, fora = c["words"], set()
        for j, w in enumerate(ws):
            if nrm(w["w"]).startswith("gratuit") or nrm(w["w"]) in ("graça", "graca") or (nrm(w["w"]) in ("custo", "cobrança") and j and nrm(ws[j - 1]["w"]) == "sem"):
                fora.add(j)
                if j and nrm(ws[j - 1]["w"]) in ("de", "sem"): fora.add(j - 1)
        if fora:
            c["words"] = [w for j, w in enumerate(ws) if j not in fora]
            if ws[max(fora)]["w"][-1:] in ".,!?;:" and c["words"]: c["words"][-1] = dict(c["words"][-1], w=c["words"][-1]["w"].rstrip(".,!?;:") + ws[max(fora)]["w"][-1])
    chunks = [c for c in chunks if c["words"]]
for i in range(len(chunks) - 1):
    if chunks[i + 1]["s"] - chunks[i]["e"] < 0.6: chunks[i]["e"] = chunks[i + 1]["s"]

# ---------- anchors ----------
def t_of(word, after=0.0, nth=0):
    hits = [w["s"] for w in W if w["s"] >= after and w["w"].lower().strip(".,!?;:") == word.lower().strip(".,!?;:")]
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

# ---------- estilo: cada variante e sorteada por padrao; o Casil fixa a que quiser em "estilo" ----------
# {"abertura": "sorteio" | "texto" | "brasao", "legenda": "sorteio" | "dourada" | "caixa"}. O sorteio usa uma
# semente tirada da propria fala, entao o mesmo video sai sempre igual ao ser renderizado de novo.
import hashlib, random
VARIANTES = {"abertura": ["texto", "brasao"], "legenda": ["dourada", "caixa"]}
est = dict(cfg.get("estilo") or {})
if "legenda" in cfg and "legenda" not in est: est["legenda"] = cfg["legenda"]   # campo antigo, fixa a legenda
semente = cfg.get("semente", int(hashlib.sha256(" ".join(w["w"] for w in words).encode()).hexdigest()[:12], 16))
rng = random.Random(semente)
estilo = {}; sorteados = []
for k, ops in VARIANTES.items():
    v = est.get(k, "sorteio")
    if v == "sorteio" or v not in ops:
        if v not in ("sorteio",): print(f"aviso: estilo.{k} = {v!r} nao existe; sorteando entre {ops}")
        v = rng.choice(ops); sorteados.append(k)
    estilo[k] = v
# visual: "formal" (padrao, o estilo de sempre) ou "dinamico" (teste aprovado em 02/10/2026: texto por tras da
# pessoa na abertura, selo do brasao, legenda que pula com marca-texto, corte a cada frase com chicote, corte
# seco e soco de zoom, adesivos, palavras que caem, claroes e efeitos sonoros). Nao e sorteado
VISUAL = est.get("visual", cfg.get("visual", "formal"))
if VISUAL not in ("formal", "dinamico"):
    print(f"aviso: estilo.visual = {VISUAL!r} nao existe; fica o formal"); VISUAL = "formal"
if VISUAL == "dinamico" and DEITADO:
    print("visual dinamico ainda so em pe: fica o formal"); VISUAL = "formal"
estilo["visual"] = VISUAL
if VISUAL == "dinamico":   # a abertura do dinamico e o selo (com o texto por tras); o brasao central nao entra
    estilo["abertura"] = "selo" if cfg.get("badge") else "texto"
    if "abertura" in sorteados: sorteados.remove("abertura")
_ab = cfg["abertura_brasao"] if isinstance(cfg.get("abertura_brasao"), dict) else {}
if estilo["abertura"] == "brasao" and not _ab.get("img", cfg.get("badge")):
    print("abertura com brasao sem 'badge' no config: fica a abertura de texto"); estilo["abertura"] = "texto"
print("estilo:", ", ".join(f"{k}={v} ({'sorteio' if k in sorteados else 'escolhido'})" for k, v in estilo.items()))

# ---------- abertura com brasao central: o brasao do orgao entra grande na metade inferior e voa para o
# canto superior direito, onde vira a logo fixa do orgao. O texto vem de "abertura_brasao" ou, na falta,
# do texto grande de abertura, que ele substitui (o gancho continua na tela, embaixo do brasao) ----------
abertura = None
if estilo["abertura"] == "brasao":
    ab = dict(cfg["abertura_brasao"]) if isinstance(cfg.get("abertura_brasao"), dict) else {}
    img = ab.get("img", cfg.get("badge"))
    first = cards[0] if cards and cards[0]["t"] < 0.3 else None
    if first and not (ab.get("kicker") or ab.get("titulo")):
        ab.setdefault("kicker", first["kicker"]); ab.setdefault("titulo", first["title"])
        ab.setdefault("dur", max(2.2, min(3.0, first["dur"]))); cards.remove(first)
    try:
        from PIL import Image
        iw, ih = Image.open(img if os.path.isabs(img) else os.path.join(proj, img)).size
    except Exception:
        iw, ih = 1, 1
    linhas = (ab.get("titulo") or "").count("<br>") + 1 if ab.get("titulo") else 0
    # grande: e a logo do orgao ocupando a tela no primeiro segundo (pedido do Casil, 02/10/2026)
    bloco = (28 + linhas * 94 + 20) if (ab.get("titulo") or ab.get("kicker")) else 0
    w0 = ab.get("largura", (380 if linhas <= 1 else 330) if not DEITADO else (220 if linhas <= 1 else 180))
    h0 = round(w0 * ih / iw)
    lim = 760 - 40 - bloco if not DEITADO else 9999   # cabe na metade inferior com o nome embaixo
    if h0 > lim: w0 = round(w0 * lim / h0); h0 = lim   # brasao alto e estreito
    # em pe: centralizado na metade inferior (de 1120 a 1880; a legenda some enquanto ele esta la);
    # deitado: centralizado na altura do painel da direita
    y0 = ab.get("y", max(170, round((VH - h0 - 20 - bloco) / 2)) if DEITADO
                else max(1100, round(1120 + (760 - h0 - 20 - bloco) / 2)))
    abertura = {"img": img, "kicker": ab.get("kicker", ""), "titulo": ab.get("titulo", ""), "t": T(ab.get("de"), 0.15),
                "dur": ab.get("dur", 2.4), "w": w0, "h": h0, "y": y0, "cx": 1510 if DEITADO else 540,
                "w1": cfg.get("badge_width", 200)}
    ab_end = abertura["t"] + abertura["dur"] + 0.75
    # o texto grande seguinte espera o brasao pousar no canto
    for c in cards:
        if c["t"] < ab_end and c["t"] + c["dur"] > abertura["t"]:
            fim = c["t"] + c["dur"]; c["t"] = round(ab_end, 3); c["dur"] = round(max(1.2, fim - ab_end), 3)
    intro_end = max(intro_end, ab_end)

# ---------- visual dinamico, abertura: o selo do brasao salta na metade inferior e o assunto aparece em letras
# gigantes POR TRAS da pessoa (precisa do recorte do recortar.py; sem ele, so o selo) ----------
dinamico = None
# o dinamico varia a cada video (pedido do Casil, 02/10/2026: "varie os motion graphs sempre pra nao ficar tudo
# igual"): o sorteio usa a semente da fala, entao o mesmo video sai sempre igual ao ser renderizado de novo
rv = random.Random(semente + 7)
if VISUAL == "dinamico":
    first = cards[0] if cards and cards[0]["t"] < 0.3 else None
    plain = lambda x: re.sub(r"<[^>]+>", " ", x or "").split()
    sem_peso = {"QUE", "DOS", "DAS", "COM", "SEM", "POR", "UMA", "PARA", "NOS", "NAS", "SUA", "SEU"}
    atras = cfg.get("abertura_atras") or [w.upper() for w in plain(first["title"] if first else "")
                                          if len(w) > 2 and w.upper() not in sem_peso][:2]
    # o recorte cobre o comeco do primeiro trecho da EDL
    i0 = int(edl[0]["src"] * FPS) + 1; n_cut = 0
    while os.path.exists(os.path.join(proj, "cut_frames", f"c{i0 + n_cut:05d}.png")): n_cut += 1
    cut_until = round(min(3.0, edl[0]["dur"] - 0.1, n_cut / FPS - 0.1), 2) if n_cut else 0.0
    if cut_until < 1.5: cut_until = 0.0; atras = []
    if not atras and cfg.get("abertura_atras") is None and n_cut == 0:
        print("dinamico: sem cut_frames (rode o recortar.py): a abertura fica sem o texto por tras")
    selo = None
    if cfg.get("badge"):
        kick = (first["kicker"] if first else "") if atras else " ".join(plain(first["title"] if first else ""))
        selo = {"img": cfg["badge"], "t": 0.35, "fim": round(max(2.4, cut_until - 0.25) if atras else 2.75, 2), "texto": kick}
    if first and (atras or selo): cards.remove(first)
    VAR = {"marca": ["caixa", "sublinhado", "cor"], "atras": ["sobe", "zoom", "letra"], "tema": ["branco", "grafite", "dourado"],
           "numero": ["circulo", "sublinhado", "raios"], "queda": ["queda", "sobe", "giro"]}
    var = {k: rv.choice(ops) for k, ops in VAR.items()}
    var.update({k: v for k, v in (cfg.get("dinamico_var") or {}).items() if v in VAR.get(k, [])})
    dinamico = {"atras": atras, "cutPrefix": "cut_frames/c", "cutUntil": cut_until if atras else 0.0, "selo": selo, "var": var}
    print("dinamico: variacao", ", ".join(f"{k}={v}" for k, v in var.items()))
    intro_end = max(intro_end, (selo["fim"] + 0.4) if selo else 0.0, cut_until)
    print(f"dinamico: texto por tras {atras or 'nao'} ate {cut_until}s, selo {'sim' if selo else 'nao'}")

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
    # nem o brasao central da abertura, que ocupa a mesma area
    if abertura and t0 < abertura["t"] + abertura["dur"] + 0.1: t0 = abertura["t"] + abertura["dur"] + 0.1
    if dinamico and dinamico["selo"] and t0 < dinamico["selo"]["fim"] + 0.2: t0 = dinamico["selo"]["fim"] + 0.2
    d = dict(sc); d.pop("from", None); d.pop("to", None)
    if d.get("type") == "documento": d["type"] = "prova"   # decisao, edital, gabarito: a mesma cena da folha
    # cena "prova": a folha da questao em tela cheia, com marca-texto, circulo, seta e carimbo ancorados na fala.
    # So com o print REAL da questao ("img"); a folha-modelo e so para teste e sai com a marca SIMULACAO
    if d.get("type") in ("prova", "ranking") and DEITADO:
        print(f"cena {d['type']} ainda so em pe: fica de fora"); continue
    if d.get("type") == "prova" and not d.get("img") and not d.get("simulacao"):
        print("cena prova sem 'img' (o print da questao): fica de fora"); continue
    for k in ("marca", "circulo", "carimbo", "sobe"):
        if d.get(k) is not None:
            try: d[k] = round(T(d[k]), 3)
            except SystemExit as e: print(f"cena {d.get('type')}: {k} fora,", e); d.pop(k)
    # documento com movimento: a camera para em cada trecho citado ("paradas", com numero opcional) e etiquetas
    # pulam com a fala ("chamadas"). No dinamico, o rosto dele fica numa bolha no canto (bolha: false tira)
    for k in ("paradas", "chamadas"):
        lst = []
        for x in d.get(k) or []:
            try: lst.append(dict(x, at=round(T(x["at"]), 3)))
            except SystemExit as e: print(f"cena {d.get('type')}: {k} fora,", e)
        if lst: d[k] = sorted(lst, key=lambda x: x["at"])
        else: d.pop(k, None)
    if d.get("type") == "prova" and d.get("img") and d.get("bolha") is None: d["bolha"] = VISUAL == "dinamico"
    if d.get("type") == "ranking" and d.get("sobe") is None: d["sobe"] = round(t0 + 1.0, 3)
    if "stagger" in d: d["stagger"] = [T(x) - t0 if isinstance(x, dict) else x for x in d["stagger"]]
    d.update({"t": round(t0, 3), "dur": round(t1 - t0, 3)})
    if d["dur"] > 0.4: scenes.append(d)

# ---------- a area dos infograficos (metade inferior; deitado, o painel da direita) e o nosso diferencial
# (nenhum concorrente usa infografico): avisar buracos ----------
occ = sorted([(s["t"], s["t"] + s["dur"]) for s in scenes] + [(c["t"], c["t"] + c["dur"]) for c in cards]
             + ([(abertura["t"], abertura["t"] + abertura["dur"] + 0.75)] if abertura else []))
gap_from = intro_end
for a, b in occ:
    if a - gap_from > cfg.get("max_vazio", 2.0) and gap_from < outro_at:
        print(f"aviso: {AREA} de {gap_from:.1f}s a {min(a, outro_at):.1f}s; acrescente uma cena")
    gap_from = max(gap_from, b)
if outro_at - gap_from > cfg.get("max_vazio", 2.0):
    print(f"aviso: {AREA} de {gap_from:.1f}s a {outro_at:.1f}s; acrescente uma cena")

# ---------- rosto bruto (sem zoom): mede onde fica a cabeca para a camera e o layout se ajustarem a
# ele. Sem OpenCV, tudo segue o padrao ----------
face_tops, face_bots, face_cy = [], [], []
try:
    import cv2
    casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    for i in range(1, frame_count + 1, max(1, frame_count // 16)):
        g = cv2.imread(os.path.join(frames_dir, f"f{i:05d}.jpg"), cv2.IMREAD_GRAYSCALE)
        if g is None: continue
        fs = casc.detectMultiScale(g, 1.1, 6, minSize=(VW // 9, VW // 9))
        if len(fs):
            x, y, w, h = max(fs, key=lambda f: f[2] * f[3])
            face_tops.append(y - 0.3 * h); face_bots.append(y + 1.15 * h)   # cabelo em cima, queixo e barba embaixo
            face_cy.append(y + 0.5 * h)
except Exception as e:
    print("rosto: deteccao indisponivel,", type(e).__name__)
face_tops.sort(); face_bots.sort(); face_cy.sort()
tem_rosto = len(face_tops) >= 3
# camera ajustada ao rosto, como nas edicoes manuais de out/2026: rosto grande no quadro pede zooms menores
# (senao cai no "so a cabeca", recusado) e o centro do zoom na altura do rosto (senao o zoom corta a testa).
# Valores do config.json valem sempre; isto so preenche o que faltar.
pivot = cfg.get("pivot")
nivel_auto = None
if tem_rosto and not DEITADO:
    alt_rosto = (face_bots[-1 - len(face_bots) // 10] - face_tops[len(face_tops) // 10]) / VH
    if pivot is None:
        pivot = [50, round(max(18, min(42, face_cy[len(face_cy) // 2] / VH * 100)))]
    if alt_rosto > 0.42: nivel_auto = ([1.0, 1.08, 1.0, 1.15, 1.08, 1.0], 1.1)
    elif alt_rosto > 0.32: nivel_auto = ([1.0, 1.12, 1.0, 1.22, 1.12, 1.0], 1.12)
    print(f"camera: rosto ocupa {alt_rosto:.0%} da altura, pivo {pivot}"
          + (f", enquadramentos {nivel_auto[0][:4]} e zoom-hit {nivel_auto[1]}" if nivel_auto and "framings" not in cfg else ""))

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
levels = cfg.get("framings", nivel_auto[0] if nivel_auto else [1.0, 1.13, 1.0, 1.26, 1.13, 1.0, 1.26, 1.0, 1.13, 1.26, 1.0, 1.13])
shots = [{"t": bounds[i], "end": bounds[i + 1], "scale": levels[i % len(levels)],
          "drift": 0.06 if levels[i % len(levels)] > 1.0 else 0.035} for i in range(len(bounds) - 1)]
# visual dinamico: um plano por frase (2,2 s no minimo), trocando o enquadramento com chicote, corte seco com
# tremor ou soco de zoom; as cenas comecam em plano novo, com chicote
if VISUAL == "dinamico":
    lv = cfg.get("framings", nivel_auto[0][:4] if nivel_auto else [1.0, 1.12, 1.04, 1.18])
    inicios = [round(s["t"], 2) for s in scenes]
    cand = sorted(set([round(c["s"], 2) for c in chunks] + inicios))
    ini0 = max(dinamico["cutUntil"] + 0.15, 1.2) if dinamico else 1.2
    cortes, ult = [], 0.0
    for c in cand:
        if c < ini0 or c >= outro_at - 0.5: continue
        if c - ult >= 2.2 or (c in inicios and c - ult >= 1.2): cortes.append(c); ult = c
    shots, a, lado, ant = [], 0.0, 1, None
    for i, c in enumerate(cortes + [round(out_total, 3)]):
        tr = None
        if i > 0:
            # entrada de cena: chicote; no resto, a sequencia sorteada, sem repetir a troca anterior
            tr = "whip" if (a in inicios or i == 1) else rv.choice([x for x in ("corte", "punch", "whip") if x != ant])
            if tr == "whip": lado = rv.choice([-1, 1])
            ant = tr
        shots.append({"t": a, "end": c, "scale": lv[i % len(lv)], "drift": 0.04, "tr": tr, "dir": lado}); a = c
    # cada adesivo entra de um jeito, nunca igual ao anterior, e a inclinacao alterna de lado
    ult, lado_t = None, rv.choice([-1, 1])
    for sc in scenes:
        if sc.get("type") == "prova": continue
        sc["anim"] = rv.choice([x for x in ("mola", "queda", "lateral", "carimbo") if x != ult]); ult = sc["anim"]
        sc["tilt"] = round(rv.uniform(1.5, 3.2) * lado_t, 1); lado_t = -lado_t
hits = []
for h in cfg.get("hits", []):
    try: t = T(h)
    except SystemExit as e: print("skip hit:", e); continue
    if any(k["t"] - 0.3 <= t <= k["t"] + k["dur"] + 0.3 for k in cards): continue
    hits.append({"t": round(t - 0.05, 3), "dur": cfg.get("hit_dur", 1.1), "scale": cfg.get("hit_scale", nivel_auto[1] if nivel_auto else 1.2)})
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
if abertura: abertura["img"] = P(abertura["img"])
if dinamico and dinamico["selo"]: dinamico["selo"]["img"] = P(dinamico["selo"]["img"])
for sc in scenes:
    if sc.get("type") == "prova" and sc.get("img"):
        sc["img"] = P(sc["img"])
        try:
            from PIL import Image
            sc["iw"], sc["ih"] = Image.open(sc["img"]).size
        except Exception as e:
            print("cena prova: imagem ilegivel,", e)
# titulo fixo no alto: o assunto do video visivel do inicio ao encerramento (padrao dos reels que mais
# engajaram nos concorrentes); "chamada" e a linha menor embaixo, ex. "Explico na legenda"
# ---------- rosto: onde fica a cabeca (com o zoom maximo dos planos), para o titulo e a legenda nao
# cobrirem o rosto. Reel do PMES com avatar (02/10/2026): o titulo e o "Explico na legenda" caiam na testa.
# Deteccao opcional: sem OpenCV, segue o layout padrao ----------
rosto = None
if tem_rosto:
    smax = max([x["scale"] for x in shots] + [h["scale"] for h in hits] + [1.0])
    py = VH * (pivot or [50, 38])[1] / 100
    top, bot = face_tops[len(face_tops) // 10], face_bots[-1 - len(face_bots) // 10]
    rosto = {"topo": int(py + (top - py) * smax), "base": int(py + (bot - py) * smax)}
    print(f"rosto: de {rosto['topo']} a {rosto['base']} px (com zoom {smax:.2f})")

titulo = None
if cfg.get("titulo"):
    tc = cfg["titulo"] if isinstance(cfg["titulo"], dict) else {"texto": cfg["titulo"]}
    titulo = {"texto": tc["texto"], "chamada": tc.get("chamada"), "t": T(tc.get("de"), intro_end)}
    if tc.get("topo") is not None: titulo["topo"] = tc["topo"]
    if tc.get("alinhar"): titulo["alinhar"] = tc["alinhar"]
    # em pe, o titulo fica em 300 px, centralizado. Se ali ele cobre a cabeca, sobe para a barra do alto,
    # entre a logo do escritorio e a do orgao, compacto; se ainda assim nao couber, a chamada sai
    if rosto and not DEITADO and "topo" not in titulo:
        n = len(re.sub(r"<[^>]+>", "", tc["texto"]))
        alt = 40 + 61 * (1 if n <= 30 else 2) + (60 if titulo["chamada"] else 0)
        if 300 + alt > rosto["topo"] - 10:
            larg = VW - 380 - (52 + (cfg.get("badge_width") or 200) + 24) - 52
            linhas_t = -(-n * 22 // max(200, larg))   # ~22 px por caractere em 38 px
            alt_c = 29 + 43 * linhas_t + (44 if titulo["chamada"] else 0)
            titulo.update({"topo": 56, "alinhar": "barra", "compacto": True})
            if 56 + alt_c > rosto["topo"] - 6 and titulo["chamada"]:
                titulo["chamada"] = None
                print("titulo: a chamada saiu para nao cobrir a cabeca")
            print(f"titulo: subiu para a barra do alto (a cabeca comeca em {rosto['topo']} px)")
# legenda: abaixo do queixo. A caixa tem 230 px e o texto encosta embaixo; em duas linhas ele comeca
# ~60 px abaixo do topo da caixa. Desce no maximo ate 1200 (a base da caixa encosta nos infograficos, em 1440)
cap_top = 1160
if rosto and not DEITADO and rosto["base"] + 20 > cap_top + 60:
    cap_top = min(1200, rosto["base"] - 40)
    print(f"legenda: desceu para {cap_top} px (o queixo vai ate {rosto['base']} px)")
    if rosto["base"] + 20 > cap_top + 60: print("aviso: o rosto desce ate a legenda; baixe os framings ou o pivot")
# palavras-chave: marca-texto na legenda do dinamico. As do config ou, na falta, os numeros e as palavras
# dos textos grandes, das cenas e do titulo
def _n(x):
    import unicodedata
    x = unicodedata.normalize("NFD", x.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(ch for ch in x if unicodedata.category(ch) != "Mn"))
VAZIAS = {"para", "pela", "pelo", "como", "mais", "isso", "esse", "essa", "este", "esta", "voce", "sua", "seu", "suas",
          "seus", "que", "dos", "das", "nos", "nas", "com", "sem", "uma", "por", "tem", "temos", "ainda", "pode", "fale"}
if cfg.get("palavras_chave"):
    chave = {_n(w) for w in cfg["palavras_chave"]}
else:
    fontes_txt = [c["title"] for c in cards] + [str(sc.get(k) or "") for sc in scenes for k in ("head", "value", "unit")]
    fontes_txt += [titulo["texto"]] if titulo else []
    fontes_txt += (dinamico or {}).get("atras") or []
    chave = {_n(w) for t_ in fontes_txt for w in re.sub(r"<[^>]+>", " ", t_).split()}
    chave = {w for w in chave if (w.isdigit() or len(w) >= 4) and w not in VAZIAS}
for c in chunks:
    for w in c["words"]: w["k"] = _n(w["w"]) in chave
# efeitos sonoros por evento (assemble.py): estalo nas entradas, chicote e tique nas trocas de plano, impacto
# no numero, no carimbo e nas palavras que caem, risco de caneta no circulo
sfx = []
for sc in scenes:
    if sc.get("type") == "prova":
        sfx += [{"k": "whoosh", "t": sc["t"] - 0.2}, {"k": "whoosh", "t": sc["t"] + sc["dur"] - 0.2}]
        if sc.get("marca") is not None: sfx.append({"k": "tick", "t": sc["marca"]})
        if sc.get("circulo") is not None: sfx.append({"k": "scratch", "t": sc["circulo"]})
        if sc.get("carimbo") is not None: sfx.append({"k": "boom", "t": sc["carimbo"]})
    elif sc.get("type") == "ranking":
        sfx += [{"k": "pop", "t": sc["sobe"]}, {"k": "tick", "t": sc["sobe"] + 0.4}, {"k": "tick", "t": sc["sobe"] + 0.65}]
    elif VISUAL == "dinamico":
        sfx.append({"k": "boom" if sc.get("type") == "counter" else "pop", "t": sc["t"] + 0.05})
if VISUAL == "dinamico":
    cut_in = lambda x: any(sc.get("type") == "prova" and sc["t"] - 0.3 <= x <= sc["t"] + sc["dur"] for sc in scenes)
    for s_ in shots[1:]:
        x = s_["t"] - (0.12 if s_["tr"] == "whip" else 0)
        if not cut_in(x): sfx.append({"k": {"whip": "whoosh", "corte": "tick"}.get(s_["tr"], "pop"), "t": x})
    for c in cards:
        nw = len(re.sub(r"<br>", " ", c["title"]).split())
        for j in range(nw): sfx.append({"k": "boom" if j == nw - 1 else "tick", "t": c["t"] + 0.1 + j * 0.16})
    if dinamico and dinamico["selo"]: sfx.append({"k": "pop", "t": dinamico["selo"]["t"]})
    sfx.append({"k": "whoosh", "t": outro_at - 0.2})
sfx.sort(key=lambda x: x["t"])
tl = {"fps": FPS, "frameCount": frame_count, "framePrefix": cfg.get("frames", "src_frames") + "/f", "total": round(out_total, 2),
      "edl": edl, "chunks": chunks, "cards": cards, "scenes": scenes, "shots": shots, "hits": hits, "inserts": inserts,
      "cuts": edl_cuts, "introEnd": round(intro_end, 2), "outroAt": round(outro_at, 2),
      "outFrames": os.path.join(proj, "out_frames"), "brand": brand, "badge": P(cfg.get("badge")), "badgeWidth": cfg.get("badge_width"),
      "source": os.path.join(proj, cfg["video"]), "pivot": pivot, "titulo": titulo,
      "abertura": abertura, "legenda": estilo["legenda"], "estilo": estilo,
      "formato": "deitado" if DEITADO else "em_pe", "W": VW, "H": VH, "rosto": rosto, "capTop": cap_top,
      # do reel na rua que o Casil aprovou (out/2026): zoom de entrada e transicao em zoom entre os planos
      "transicao": cfg.get("transicao", "corte"), "entradaZoom": cfg.get("entrada_zoom"),
      "visual": VISUAL, "dinamico": dinamico, "sfx": sfx}
json.dump(tl, open(os.path.join(proj, "timeline.json"), "w"), ensure_ascii=False, indent=1)
print("cards", [(round(c["t"], 2), c["title"].replace("<br>", " ")) for c in cards])
print("scenes", [(round(s["t"], 2), round(s["dur"], 2), s["type"]) for s in scenes])
print("shots", [(round(x["t"], 1), x["scale"]) for x in shots], "hits", len(hits), "outro", tl["outroAt"], "total", tl["total"])
