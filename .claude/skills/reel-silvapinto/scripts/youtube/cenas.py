"""Peças para montar o scenes.json de um vídeo do YouTube (16:9), no formato aprovado em 04/10/2026.

O vídeo do YouTube NÃO recorta o apresentador nem desfoca as laterais: ele aparece sempre com o fundo
original da gravação (clone ou câmera), numa faixa lateral (P) ou em close (X), e a edição alterna em
cortes com imagens do assunto (B), documentos (D) e infográficos (I). O dono aprovou isso em 04/10 e
recusou, depois de testar, o recorte, o fundo ampliado e o estilo "jornal" feito no HyperFrames.

Uso, dentro da pasta do projeto (com fr/, rosto.json, img/, clips/):

    import sys; sys.path.insert(0, "<skill>/scripts/youtube")
    from cenas import *
    abrir(".")                       # lê rosto.json e conta os clipes
    cenas = [B(0, 4.35, ..., photo="viaturas.jpg", credit=...), P(4.35, 8.95, "R", ...), ...]
    gravar(cenas)                    # confere se são contíguas e grava scenes.json (+ cartão final)

Os tempos são os da fala já cortada (fr/ e audio), em segundos. Cada elemento que entra no tempo de uma
palavra usa a(t): pegue t das palavras transcritas (transcribe.py), nunca de chute.
"""
import json
import os
import statistics

FPS = 24
LOGO = "__ASSETS__/brand/logo_mono.png"
_R = {}
_NCLIP = {}


def abrir(pasta="."):
    global _R
    os.chdir(pasta)
    _R = json.load(open("rosto.json"))
    if os.path.isdir("clips"):
        for k in os.listdir("clips"):
            if os.path.isdir(f"clips/{k}"):
                _NCLIP[k] = len(os.listdir(f"clips/{k}"))
    return len(_R["cy"]) / FPS


def _med(key, t0, t1):
    n = len(_R[key])
    a, b = int(t0 * FPS), max(int(t0 * FPS) + 1, int(t1 * FPS))
    return statistics.median(_R[key][a:min(b, n)])


# ── layouts ─────────────────────────────────────────────────────────────────
def P(t0, t1, side, html, nome=False):
    """Apresentador numa faixa de 860 px (side 'L' ou 'R'), conteúdo do outro lado sobre o escritório desfocado."""
    cy = _med("cy", t0, t1)
    vis = 1080 / (860 / 1080)
    off = max(0, min(1920 - vis, cy - 0.40 * vis))
    return dict(t0=t0, t1=t1, layout="P", side=side, html=html, off=round(off), nome=nome)


def X(t0, t1, html=""):
    """Close no rosto, tela cheia. Amplia a fonte 1,78x (fica mais mole): só em frases de ênfase, até ~7 s."""
    return dict(t0=t0, t1=t1, layout="X", html=html, cx=_med("cx", t0, t1), cy=_med("cy", t0, t1) - 30)


def B(t0, t1, html, photo=None, kb=None, clips=None, credit="", grad="grad-b"):
    """Imagem de apoio em tela cheia: foto com Ken Burns (kb=[z0,z1,x0,x1,y0,y1]) ou clipes em sequência
    (clips=[(nome, duração), ...], de clips/<nome>/c0001.jpg...). Crédito CC sempre que for de terceiro."""
    d = dict(t0=t0, t1=t1, layout="B", html=html, credit=credit, grad=grad)
    if photo:
        d.update(photo=photo, kb=kb or [1.0, 1.08, 0, 0, 0, 0])
    if clips:
        d["clips"] = [[c, dur, _NCLIP[c]] for c, dur in clips]
    return d


def I(t0, t1, html, photo=None, kb=None, credit=""):
    """Infográfico em tela cheia, sobre o escritório desfocado ou sobre uma foto escurecida."""
    d = dict(t0=t0, t1=t1, layout="I", html=html, credit=credit)
    if photo:
        d.update(photo=photo, kb=kb or [1.0, 1.06, 0, 0, 0, 0])
    return d


def D(t0, t1, html, doc, credit=""):
    """Documento com câmera: doc = dict(img, w, h, cam=[[t_local, x, y, zoom], ...],
    marcas=[dict(r=[x, y, w, h], at=t_absoluto)]). Coordenadas em pixels da imagem."""
    return dict(t0=t0, t1=t1, layout="D", html=html, doc=doc, credit=credit)


# ── elementos de texto ──────────────────────────────────────────────────────
def a(t, an="up", d=0.45):
    """Entrada animada no tempo t (absoluto): up | left | pop | wipe | fade."""
    return f'data-at="{t}" data-a="{an}" data-d="{d}"'


def tag(txt, t):
    return f'<div class="tag" {a(t, "left")}>{txt}</div>'


def chk(n, txt, t, ic=None):
    bolinha = f'<span class="bola">{{ic:{ic}}}</span>' if ic else f'<span class="num">{n}</span>'
    return f'<div class="item" {a(t, "left")}>{bolinha}<span>{txt}</span></div>'


def final(t0, dur=3.6):
    return dict(t0=t0, t1=t0 + dur, layout="O",
                html=f'<img src="{LOGO}" style="height:150px" {a(t0 + 0.1, "pop", .6)}>'
                     f'<div class="h2" style="margin-top:26px" {a(t0 + 0.5)}>Silva Pinto <span class="g">Advocacia</span></div>'
                     f'<div class="tag" style="margin-top:14px" {a(t0 + 0.8, "fade")}>Concursos públicos</div>'
                     f'<div class="sub" style="font-size:24px;margin-top:40px;color:rgba(255,255,255,.7)" {a(t0 + 1.1, "fade")}>'
                     f'Conteúdo informativo. Cada caso é analisado individualmente.</div>')


def gravar(cenas, com_final=True):
    fim = len(_R["cy"]) / FPS
    if com_final and cenas[-1]["layout"] != "O":
        cenas = cenas + [final(fim)]
    for x, y in zip(cenas, cenas[1:]):
        assert abs(x["t1"] - y["t0"]) < 1e-6, f"buraco ou sobreposição entre {x['t0']} e {y['t0']}"
    total = cenas[-1]["t1"]
    json.dump(dict(scenes=cenas, nFrames=len(_R["cy"]), total=total), open("scenes.json", "w"), ensure_ascii=False)
    print(len(cenas), "cenas,", round(total, 2), "s")
