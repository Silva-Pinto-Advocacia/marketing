"""Estilo misto, passo 1: quadros da fala, rosto e recortes de b-roll.

    python3 preparar.py <projeto>            # tudo
    python3 preparar.py <projeto> broll      # só refaz os recortes de b-roll (depois de mudar broll.json)
    python3 preparar.py <projeto> rosto      # só refaz o rosto.json

Lê <projeto>/fala.mov (a fala já cortada, 1920x1080, 30 fps) e <projeto>/broll.json:
    {"gabarito": {"arquivo": "clips/20468.mp4", "ini": 8, "dur": 5, "x": 200, "x9": 480}, ...}
`x` é o deslocamento do recorte do painel (1080x880) e `x9` o do recorte em pé (1080x1920), em pixels do
arquivo original; sem eles, o recorte fica no centro. `dur` deve cobrir a cena mais longa que usa o clipe.

Grava fr/ (quadros), rosto.json (cx, cy e fw = largura do rosto, por quadro, suavizados), cl/<nome>/ e
cl9/<nome>/ (quadros dos recortes) e folha_broll.jpg (uma folha para conferir os recortes de olho).
"""
import json, os, subprocess, sys, shutil

P = os.path.abspath(sys.argv[1]); ETAPA = sys.argv[2] if len(sys.argv) > 2 else 'tudo'


def ff(*a): subprocess.run(['ffmpeg', '-v', 'error', '-y', *a], check=True)


def tamanho(arq):
    o = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
                        '-of', 'csv=p=0', arq], capture_output=True, text=True, check=True).stdout.strip().split(',')
    return int(o[0]), int(o[1])


def quadros():
    shutil.rmtree(f'{P}/fr', ignore_errors=True); os.makedirs(f'{P}/fr')
    ff('-i', f'{P}/fala.mov', '-vf', 'fps=30,scale=in_color_matrix=bt709:in_range=tv:out_color_matrix=bt470bg:out_range=pc',
       '-q:v', '2', f'{P}/fr/f%05d.jpg')


def rosto():
    import cv2, numpy as np
    fs = sorted(os.listdir(f'{P}/fr')); n = len(fs)
    cc = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    pts = {}
    for i in range(0, n, 3):
        im = cv2.imread(f'{P}/fr/{fs[i]}', 0); h0, w0 = im.shape; k = 960 / w0
        f = cc.detectMultiScale(cv2.resize(im, (960, round(h0 * k))), 1.1, 5, minSize=(50, 50))
        if len(f):
            x, y, w, h = max(f, key=lambda r: r[2] * r[3]); pts[i] = ((x + w / 2) / k, (y + h / 2) / k, w / k)
    if len(pts) < n / 30: raise SystemExit(f'rosto achado em só {len(pts)} de {n // 3} quadros: conferir a filmagem')
    # a suavização recomeça em cada emenda da fala (trechos de palavras.json): entre dois trechos ele pode
    # estar em outro lugar do quadro, e a média atravessando o corte deixaria o rosto "atrasado"
    cortes = [0, n]
    if os.path.exists(f'{P}/palavras.json'):
        cortes = sorted({0, n, *(round(g['t0'] * 30) for g in json.load(open(f'{P}/palavras.json')).get('trechos', []) if 0 < round(g['t0'] * 30) < n)})
    cx, cy, fw = np.zeros(n), np.zeros(n), np.zeros(n)
    for a0, a1 in zip(cortes, cortes[1:]):
        ks = [k for k in sorted(pts) if a0 <= k < a1] or [min(pts, key=lambda k: abs(k - a0))]
        arr = np.array([pts[k] for k in ks]); m = a1 - a0; j = min(15, m // 2); ker = np.ones(2 * j + 1) / (2 * j + 1)
        sm = lambda v: np.convolve(np.pad(np.interp(range(a0, a1), ks, v), j, mode='edge'), ker, 'valid')
        cx[a0:a1], cy[a0:a1], fw[a0:a1] = sm(arr[:, 0]), sm(arr[:, 1]), sm(arr[:, 2])
    json.dump(dict(cx=cx.round(1).tolist(), cy=cy.round(1).tolist(), fw=fw.round(1).tolist()), open(f'{P}/rosto.json', 'w'))
    print(f'rosto: {len(pts)} detecções; cx {cx.min():.0f}-{cx.max():.0f}, cy {cy.min():.0f}-{cy.max():.0f}, largura {fw.min():.0f}-{fw.max():.0f}')


def broll():
    B = json.load(open(f'{P}/broll.json'))
    for d in ('cl', 'cl9'): shutil.rmtree(f'{P}/{d}', ignore_errors=True)
    for nome, c in B.items():
        arq = c['arquivo'] if os.path.isabs(c['arquivo']) else f"{P}/{c['arquivo']}"; w, h = tamanho(arq)
        wp, w9 = round(h * 1080 / 880), round(h * 9 / 16)            # largura dos recortes no original
        xp = c.get('x', (w - wp) // 2); x9 = c.get('x9', (w - w9) // 2)
        nitidez = ',unsharp=5:5:0.6' if h < 1300 else ''               # 720p esticado para 1920 precisa de um pouco
        for d, cw, cx, esc in (('cl', wp, xp, '1080:880'), ('cl9', w9, x9, '1080:1920')):
            os.makedirs(f'{P}/{d}/{nome}')
            ff('-ss', str(c.get('ini', 0)), '-t', str(c.get('dur', 5)), '-i', arq, '-vf',
               f"fps=30,crop={cw}:{h}:{max(0, min(cx, w - cw))}:0,scale={esc}:flags=lanczos{nitidez if d == 'cl9' else ''}",
               '-q:v', '3', f'{P}/{d}/{nome}/c%04d.jpg')
        print(f"{nome}: {len(os.listdir(f'{P}/cl9/{nome}'))} quadros ({w}x{h})")
    from PIL import Image
    ns = list(B); s = Image.new('RGB', (180 * len(ns), 320 + 147), '#111')
    for i, n in enumerate(ns):
        s.paste(Image.open(f'{P}/cl9/{n}/c0030.jpg').resize((180, 320)), (i * 180, 0))
        s.paste(Image.open(f'{P}/cl/{n}/c0030.jpg').resize((180, 147)), (i * 180, 320))
    s.save(f'{P}/folha_broll.jpg')


if ETAPA == 'tudo': quadros()
if ETAPA in ('tudo', 'rosto'): rosto()
if ETAPA in ('tudo', 'broll') and os.path.exists(f'{P}/broll.json'): broll()
