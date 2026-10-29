"""Estilo misto, passo 2: peças para escrever as cenas de um reel (usar no cenas.py do projeto).

O cenas.py do projeto descreve os TRECHOS (beats) da fala, cada um com um tipo, o b-roll que combina e o
HTML do texto/infográfico; `escrever()` sorteia o layout de cada trecho (sorteio.py), monta as legendas e
grava <projeto>/cenas.json. Modelo completo: examples/misto_vsl/cenas.py.

    import sys; sys.path.insert(0, '<skill>/scripts/misto'); from misto import *
    pj = carregar('<projeto>'); T = pj.T
    BEATS = [dict(t0=0, t1=2.6, tipo='gancho', html=''), dict(..., tipo='prova', clip='juiz', html=zona(...)), ...]
    escrever(pj, BEATS, semente=7, sticker=etiqueta('ELIMINADO NO<br>CONCURSO?'), titulo_fim='A PALAVRA DA BANCA<br>NÃO É A ÚLTIMA',
             t_clica=T('clica'), brasao='<skill>/assets/brasoes/pmerj.png')
"""
import json, os, re, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ASSETS = 'file://' + os.path.abspath(f'{AQUI}/../../assets')
sys.path.insert(0, AQUI)
from sorteio import sortear  # noqa: E402

# Na abertura com etiqueta, o alto da cabeça desce até 360 px da borda de cima, para a etiqueta caber em
# cima da cabeça. Reclamação do Casil em 29/10/2026: "não termos o texto tampando meu rosto no começo do vídeo".
TOPO_ROSTO_ETIQUETA = 360


class Projeto:
    def __init__(self, pasta):
        self.pasta = os.path.abspath(pasta)
        D = json.load(open(f'{self.pasta}/palavras.json'))
        self.P = D['palavras']; self.FALA = round(D['total'], 3)
        self.TR = {g['nome']: round(g['t0'], 3) for g in D.get('trechos', [])}

    def T(self, w, after=0):
        """Início (s) da primeira palavra `w` falada depois de `after`."""
        for p in self.P:
            if p['s'] >= after - 0.05 and re.sub(r'\W', '', p['w']).lower() == w.lower(): return round(p['s'], 2)
        raise SystemExit(f'palavra "{w}" não encontrada depois de {after}s')


def carregar(pasta): return Projeto(pasta)


# ---- blocos de HTML ----------------------------------------------------------------------------------------
def a(t, an='up', d=.45): return f'data-at="{round(t, 3)}" data-a="{an}" data-d="{d}"'
def G(x): return f'<span class="g">{x}</span>'
def kick(t, txt): return f'<div class="kick" {a(t, "left")}>{txt}</div>'
def zona(inner): return f'<div class="zona">{inner}</div>'


def etiqueta(texto, kicker='atenção', t1=2.5):
    """A etiqueta branca da abertura (fica acima da cabeça; o rosto desce para ela caber)."""
    return dict(t1=t1, html=f'<small>{kicker}</small>{texto}')


def item(k, n, t, ic, txt):
    """Item k (0..n-1) de uma lista falada: pontinhos de progresso, 'situação k de n' e o cartão com ícone."""
    return zona('<div class="pontos" style="margin-bottom:22px">' + ''.join(f'<b class="{"on" if j <= k else ""}"></b>' for j in range(n)) + '</div>'
                + kick(t + .05, f'situação {k + 1} de {n}') + f'<div class="vidro" style="margin-top:18px;display:flex;align-items:center;gap:24px" {a(t + .1, "up")}>'
                f'<span class="bola" style="width:104px;height:104px;font-size:52px">{{ic:{ic}}}</span><span style="font:800 52px/1.12 Manrope">{txt}</span></div>')


def brasao_destaque(t, src, sigla, linha=''):
    """Primeira menção ao órgão do concurso: o brasão entra grande, com brilho, e a sigla embaixo.
    Depois disso ele fica no canto (escrever(..., brasao=src))."""
    src = src if src.startswith('file://') else 'file://' + os.path.abspath(src)
    return zona(f'<div style="text-align:center"><img src="{src}" style="height:250px;filter:drop-shadow(0 0 40px rgba(240,207,134,.55)) drop-shadow(0 12px 30px rgba(0,0,0,.6))" {a(t, "pop", .55)}>'
                f'<div class="h ouro" style="font-size:120px;margin-top:14px" {a(t + .25, "up")}>{sigla}</div>'
                + (f'<div class="sub" style="font-size:42px" {a(t + .45, "up")}>{linha}</div>' if linha else '') + '</div>')


def numero(t, valor, rotulo, antes='', depois='', de=0):
    """Infográfico de um número (vagas, nota de corte, candidatos): o número conta de `de` até `valor`."""
    return (f'<div class="vidro" style="text-align:center" {a(t, "up")}>{kick(t + .05, rotulo)}'
            f'<div class="h ouro" style="font-size:200px;margin-top:10px">{antes}<span data-at="{t + .15}" data-a="fade" data-d="1.1" data-cont="{de},{valor}">{de}</span>{depois}</div></div>')


def barras(t, linhas):
    """Comparação em barras: linhas = [(rótulo, fração 0..1, destaque?), ...]."""
    h = ''
    for k, (rot, fr, dest) in enumerate(linhas):
        cor = 'var(--gold)' if dest else 'rgba(255,255,255,.35)'
        h += (f'<div style="margin-top:{0 if k == 0 else 22}px" {a(t + .2 * k, "up")}><div class="sub" style="font-size:34px;margin-bottom:8px">{rot}</div>'
              f'<div class="barra"><i style="width:{fr * 100:.0f}%;background:{cor}" {a(t + .2 * k + .1, "grow", .8)}></i></div></div>')
    return f'<div class="vidro">{h}</div>'


def chamada(t, texto='Falar com a equipe'):
    return (f'<div style="position:absolute;left:0;right:0;top:640px;text-align:center"><div style="font:800 76px/1.05 Manrope;text-shadow:0 6px 30px rgba(0,0,0,.6)" {a(t, "up")}>Toque em</div>'
            f'<div style="margin-top:34px;position:relative;display:inline-block" {a(t + .35, "pop", .5)}><span class="botao">{{ic:brand-whatsapp}} {texto} ›</span><div class="toque" style="right:60px;top:20px"></div></div>'
            f'<div class="setas" style="margin-top:70px;font:400 120px/0.6 \'Bebas Neue\';color:var(--gold)" {a(t + .6, "fade")}>⌄<br>⌄</div></div>')


def cartao_final(F, titulo):
    return (f'<img src="{ASSETS}/brand/logo_lockup.png" style="width:640px" {a(F + .1, "pop", .6)}>'
            f'<div class="h ouro" style="font-size:118px;margin-top:50px" {a(F + .5, "up")}>{titulo}</div>'
            f'<div style="font:600 40px Manrope;margin-top:44px;color:rgba(255,255,255,.9)" {a(F + .9, "fade")}>Dr. Casil da Silva Pinto · OAB/RJ 189.781</div>'
            f'<div style="font:500 30px/1.35 Manrope;margin-top:26px;color:rgba(255,255,255,.65)" {a(F + 1.1, "fade")}>Conteúdo informativo. Não há promessa de resultado:<br>cada caso depende de análise individual.</div>')


# ---- legendas ----------------------------------------------------------------------------------------------
def legendas(P, sem=()):
    """Grupos de 1 a 3 palavras (até 18 letras), quebrando em pausa e pontuação; cada palavra aparece quando é dita."""
    ws = [p for p in P if f"{p['w']}@{p['s']:.2f}" not in set(sem)]
    grupos, cur = [], []
    for w in ws:
        if cur and (len(' '.join(x['w'] for x in cur + [w])) > 18 or len(cur) >= 3 or w['s'] - cur[-1]['e'] > 0.35 or re.search(r'[,.?!]$', cur[-1]['w'])):
            grupos.append(cur); cur = []
        cur.append(w)
    if cur: grupos.append(cur)
    caps = []
    for i, g in enumerate(grupos):
        t1 = g[-1]['e'] + 0.25
        if i + 1 < len(grupos): t1 = min(t1, grupos[i + 1][0]['s'])
        caps.append(dict(t0=g[0]['s'], t1=round(t1, 3), words=[dict(w=x['w'], s=x['s'], e=x['e']) for x in g]))
    return caps


# ---- montagem ----------------------------------------------------------------------------------------------
VEU_DIVIDIDA = 'linear-gradient(180deg,rgba(15,16,19,.55) 0%,rgba(15,16,19,.35) 40%,rgba(15,16,19,.92) 100%)'
NOME = {'cheio': 'full', 'broll': 'broll', 'dividida': 'split'}


def escrever(pj, beats, semente, titulo_fim, t_clica, sticker=None, brasao=None, fim_s=3.0, sem_legenda=()):
    """Sorteia o layout de cada trecho e grava <projeto>/cenas.json. O último trecho de `beats` termina onde
    começa a chamada; a chamada vai até o fim da fala + 0,5 s e o cartão final dura `fim_s`."""
    P = pj.pasta
    for x, y in zip(beats, beats[1:]): assert abs(x['t1'] - y['t0']) < 1e-6, f"buraco entre {x['t1']} e {y['t0']}"
    plano = sortear(beats, semente)
    c = []
    for b, l in zip(beats, plano):
        sc = dict(t0=b['t0'], t1=b['t1'], layout=NOME[l], html=b.get('html', ''), tipo=b['tipo'], plano=l)
        if l == 'broll': sc['clip'] = b['clip']
        if l == 'dividida':
            if b.get('clip'): sc['clip'] = b['clip']; sc['veu'] = b.get('veu', VEU_DIVIDIDA)
            if c and c[-1]['layout'] == 'full': sc['scan'] = True
        if b.get('clipOff'): sc['clipOff'] = b['clipOff']
        c.append(sc)
    if sticker:
        if c[0]['layout'] != 'full': raise SystemExit('a etiqueta da abertura pede o gancho em tela cheia')
        c[0]['topoRosto'] = TOPO_ROSTO_ETIQUETA
    T0 = beats[-1]['t1']; F = round(pj.FALA + 0.5, 3)
    c.append(dict(t0=T0, t1=F, layout='cta', plano='cta', cta=chamada(t_clica)))
    c.append(dict(t0=F, t1=F + fim_s, layout='fim', plano='fim', fim=cartao_final(F, titulo_fim)))
    conta = lambda d: {n: len(os.listdir(f'{P}/{d}/{n}')) for n in os.listdir(f'{P}/{d}')} if os.path.isdir(f'{P}/{d}') else {}
    B = json.load(open(f'{P}/broll.json')) if os.path.exists(f'{P}/broll.json') else {}
    S = dict(scenes=c, creditos={n: b['credito'] for n, b in B.items() if b.get('credito')}, caps=legendas(pj.P, sem_legenda), nclip=conta('cl'), nclip9=conta('cl9'), nFrames=len(os.listdir(f'{P}/fr')),
             fala=pj.FALA, total=round(c[-1]['t1'], 3), sticker=sticker, semente=semente,
             brasao=('file://' + os.path.abspath(brasao)) if brasao and not brasao.startswith('file://') else brasao)
    for sc in c:
        if sc.get('clip') and sc['clip'] not in (S['nclip9'] if sc['layout'] == 'broll' else S['nclip']):
            raise SystemExit(f"clipe {sc['clip']} sem recorte: rodar preparar.py")
    json.dump(S, open(f'{P}/cenas.json', 'w'), ensure_ascii=False)
    tot = sum(x['t1'] - x['t0'] for x in c[:-2])
    print(f'semente {semente}')
    for x in c: print(f"{x['t0']:6.2f}-{x['t1']:6.2f}  {x['plano']:9s} {x.get('tipo', '')} {x.get('clip', '')}")
    print('  '.join(f"{l} {round(sum(x['t1'] - x['t0'] for x in c if x['plano'] == l) / tot * 100)}%" for l in ('cheio', 'broll', 'dividida')))
    return S
