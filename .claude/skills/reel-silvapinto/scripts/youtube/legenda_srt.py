"""Legenda .srt do vídeo do YouTube a partir das palavras transcritas (transcribe.py), com os tempos da fala.

    python legenda_srt.py saida.srt parte1.json:0:297.0 [parte2.json:0:120.5:297.0 ...] [--corrige corr.json]

Cada parte é arquivo:início:fim[:deslocamento] (segundos): as palavras de início a fim entram somadas ao
deslocamento (o ponto da emenda no vídeo final). corr.json corrige o que o reconhecimento errou, conferido
contra o roteiro: [[parte, t_da_palavra, "transcrito", "certo"], ...] (t arredondado a 0,1 s, parte a partir de 0).
Exemplo da PCMG: [[0, 175.2, "5º", "quinquenal"], [0, 175.6, "Enaldo", "do"]].
Blocos de até 2 linhas de 42 caracteres e 5,5 s, quebrando no fim da frase, na vírgula ou na pausa.
"""
import json
import sys

LARG = 42
TROCA = {"recalculo": "recálculo"}
PARES = {("diário", "oficial"): ("Diário", "Oficial"), ("diário", "oficial,"): ("Diário", "Oficial,"),
         ("diário", "oficial."): ("Diário", "Oficial.")}


def palavras(arq, ini, fim, desl, corr):
    out = []
    for w in json.load(open(arq))["words"]:
        if not ini <= w["s"] < fim:
            continue
        txt = corr.get((round(w["s"], 1), w["w"]), w["w"])
        txt = TROCA.get(txt, txt)
        if out and txt[:1] in "-." and txt[1:2].isalnum():
            out[-1]["w"] += txt          # "delegada -geral", "20 .910," viram uma palavra
            out[-1]["e"] = w["e"] + desl
            continue
        out.append(dict(w=txt, s=w["s"] + desl, e=w["e"] + desl))
    for x, y in zip(out, out[1:]):
        par = PARES.get((x["w"].lower(), y["w"].lower()))
        if par:
            x["w"], y["w"] = par
    return out


def quebra(txt):
    """Duas linhas o mais iguais possível; None se não couber em 2 x LARG."""
    if len(txt) <= LARG:
        return txt
    esp = [i for i, c in enumerate(txt) if c == " "]
    if not esp:
        return None
    i = min(esp, key=lambda k: max(k, len(txt) - k - 1))
    return txt[:i] + "\n" + txt[i + 1:] if max(i, len(txt) - i - 1) <= LARG else None


def blocos(ws, maxd=5.5):
    cues, cur = [], []
    for k, w in enumerate(ws):
        cur.append(w)
        txt = " ".join(x["w"] for x in cur)
        prox = ws[k + 1] if k + 1 < len(ws) else None
        cabe = prox and quebra(txt + " " + prox["w"]) and prox["e"] - cur[0]["s"] <= maxd
        pausa = prox and prox["s"] - w["e"] > 0.6
        frase = w["w"][-1] in ".?!" and len(cur) >= 3
        virgula = w["w"][-1] in ",:;" and len(txt) > 45
        if not cabe or pausa or frase or virgula:
            cues.append(cur)
            cur = []
    return cues


def ts(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def main(argv):
    corr = []
    if "--corrige" in argv:
        k = argv.index("--corrige")
        corr = json.load(open(argv[k + 1]))
        argv = argv[:k] + argv[k + 2:]
    saida, ws = argv[0], []
    for n, spec in enumerate(argv[1:]):
        arq, ini, fim, *desl = spec.split(":")
        cn = {(t, a): b for p, t, a, b in corr if p == n}
        ws += palavras(arq, float(ini), float(fim), float(desl[0]) if desl else 0.0, cn)
    cues = blocos(ws)
    with open(saida, "w") as f:
        for i, c in enumerate(cues, 1):
            fim = c[-1]["e"] + 0.25
            if i < len(cues):
                fim = min(fim, cues[i][0]["s"] - 0.02)
            f.write(f"{i}\n{ts(c[0]['s'])} --> {ts(fim)}\n{quebra(' '.join(x['w'] for x in c)) or ' '.join(x['w'] for x in c)}\n\n")
    print(len(cues), "legendas ->", saida)


if __name__ == "__main__":
    main(sys.argv[1:])
