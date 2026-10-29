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
    try:
        plano = sortear(beats, semente)
    except SystemExit:   # nenhum plano cumpre as regras (vídeo curto demais, poucos clipes): alterna ele e a tela dividida
        plano = ['cheio' if i % 2 == 0 else 'dividida' for i in range(len(beats))]
        print('sorteio sem plano válido: alternando tela cheia e tela dividida')
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
    from PIL import Image
    fw_, fh_ = Image.open(f'{P}/fr/f00001.jpg').size
    S = dict(fonte=dict(w=fw_, h=fh_), scenes=c, creditos={n: b['credito'] for n, b in B.items() if b.get('credito')}, caps=legendas(pj.P, sem_legenda), nclip=conta('cl'), nclip9=conta('cl9'), nFrames=len(os.listdir(f'{P}/fr')),
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


# ---- do roteiro (JSON) às cenas: usado pelo motor do Redes e por quem não quiser escrever HTML --------------
CATALOGO = json.load(open(f'{AQUI}/catalogo.json', encoding='utf-8'))
ICONES = {'alert-circle', 'alert-triangle', 'building-bank', 'calendar-event', 'check', 'clipboard-check', 'file-certificate',
          'file-search', 'file-text', 'gavel', 'hourglass', 'list-check', 'news', 'route', 'scale', 'search', 'shield-check',
          'user', 'users', 'users-group', 'writing', 'x'}
TIPOS = {'gancho', 'tese', 'dado', 'prova', 'lista', 'instituicao'}


def _e(x, n=120):
    import html as _h
    return _h.escape(re.sub(r'\s+', ' ', str(x or '')).strip()[:n])


def _tam(txt, grande=150, medio=120, pequeno=96):
    n = max((len(p) for p in txt.split()), default=0); tot = len(txt)
    return grande if tot <= 11 and n <= 11 else medio if tot <= 18 and n <= 14 else pequeno


def bloco_html(b, t0, brasao=None):
    """Um bloco do roteiro em HTML. `b['tipo']`: frase, numero, lista, barras, carimbo, brasao, antes_depois.
    Os textos chegam crus (sem HTML) e são escapados aqui; `em` é o instante do destaque."""
    if not isinstance(b, dict): return ''
    tipo = b.get('tipo'); em = float(b.get('em') or t0 + .8)
    em = min(max(em, t0 + .2), t0 + 6)
    if tipo == 'frase':
        d = _e(b.get('destaque'), 40).upper()
        return zona((kick(t0 + .1, _e(b.get('kicker'), 40)) if b.get('kicker') else '')
                    + (f'<div class="sub" style="margin-top:10px" {a(t0 + .3, "left")}>{_e(b.get("texto"), 90)}</div>' if b.get('texto') else '')
                    + (f'<div class="h ouro brilho" style="font-size:{_tam(d)}px;margin-top:10px" {a(em, "pop", .5)}>{d}</div>' if d else ''))
    if tipo == 'numero':
        try: v = int(float(str(b.get('valor')).replace('.', '').replace(',', '.')))
        except (TypeError, ValueError): return ''
        return zona(numero(em, v, _e(b.get('rotulo'), 40), _e(b.get('antes'), 4), _e(b.get('depois'), 6)))
    if tipo == 'lista':
        n = max(2, min(int(b.get('n') or 3), 6)); k = max(0, min(int(b.get('k') or 1) - 1, n - 1))
        ic = b.get('icone') if b.get('icone') in ICONES else 'check'
        txt = _e(b.get('texto'), 60); dst = _e(b.get('destaque'), 30)
        if dst and dst in txt: txt = txt.replace(dst, G(dst), 1)
        return item(k, n, t0, ic, txt)
    if tipo == 'barras':
        ls = [(_e(l[0], 40), max(0.03, min(float(l[1]), 1)), bool(l[2] if len(l) > 2 else False))
              for l in (b.get('linhas') or [])[:3] if isinstance(l, (list, tuple)) and len(l) >= 2]
        return zona((kick(t0 + .1, _e(b.get('titulo'), 40)) if b.get('titulo') else '') + f'<div style="margin-top:16px">{barras(em, ls)}</div>') if ls else ''
    if tipo == 'carimbo':
        c = _e(b.get('carimbo'), 26).upper()
        return zona((f'<div class="vidro" {a(t0 + .2)}><div style="font:700 52px/1.2 Manrope">{_e(b.get("pergunta"), 70)}</div></div>' if b.get('pergunta') else '')
                    + f'<div style="margin-top:30px;text-align:center" {a(em, "stamp", .35)}><span class="carimbo" style="font-size:{86 if len(c) <= 16 else 64}px">{c}</span></div>')
    if tipo == 'brasao' and brasao:
        return brasao_destaque(em, brasao, _e(b.get('sigla'), 12).upper(), _e(b.get('linha'), 50))
    if tipo == 'antes_depois':
        return zona(f'<div style="display:flex;align-items:center;gap:20px">'
                    f'<div class="vidro" style="flex:1;text-align:center;padding:26px" {a(t0 + .2, "pop")}><div class="bola x" style="margin:0 auto 14px">{{ic:x}}</div><div class="h" style="font-size:60px">{_e(b.get("antes"), 22).upper()}</div></div>'
                    f'<div class="vidro" style="flex:1;text-align:center;padding:26px;border-color:var(--gold)" {a(em, "pop", .55)}><div class="bola" style="margin:0 auto 14px">{{ic:check}}</div><div class="h g" style="font-size:60px">{_e(b.get("depois"), 22).upper()}</div></div></div>')
    return ''


def broll_do_catalogo(pj, temas, baixar=None):
    """Grava <projeto>/broll.json com os temas usados, baixando cada clipe do catálogo para <projeto>/clips."""
    import urllib.request
    os.makedirs(f'{pj.pasta}/clips', exist_ok=True); B = {}
    for t in sorted(set(temas)):
        c = CATALOGO.get(t)
        if not c: continue
        arq = f"{pj.pasta}/clips/{c['id']}.mp4"
        if not os.path.exists(arq):
            try: (baixar or (lambda u, d: urllib.request.urlretrieve(u, d)))(c['url'], arq)
            except Exception as e:  # noqa: BLE001 - sem o clipe, o trecho fica sem b-roll
                print(f'b-roll {t} não baixou: {e}'); continue
        B[t] = dict(arquivo=f"clips/{c['id']}.mp4", ini=c['ini'], dur=c['dur'], x=c['x'], x9=c['x9'])
    json.dump(B, open(f'{pj.pasta}/broll.json', 'w'), ensure_ascii=False, indent=1)
    return B


def beats_do_roteiro(pj, roteiro, t_chamada, brasao=None, ajustes=None):
    """Os trechos do roteiro (já com `t0` em segundos da fala cortada) viram BEATS para `escrever`.
    `ajustes` vem de `ajustes_por_colisao`: {indice: 'dividida' | 'sem_bloco'}."""
    ajustes = ajustes or {}; FALA = pj.FALA
    tr = sorted([x for x in (roteiro.get('trechos') or []) if isinstance(x, dict) and isinstance(x.get('t0'), (int, float))],
                key=lambda x: x['t0'])
    tr = [x for x in tr if 1.5 <= x['t0'] <= t_chamada - 1.2]
    limpos = []
    for x in tr:                      # trecho de menos de 1,2 s não dá tempo de ler: some
        if not limpos or x['t0'] - limpos[-1]['t0'] >= 1.2: limpos.append(x)
    beats = [dict(t0=0, t1=None, tipo='gancho', html='')]
    for x in limpos:
        beats[-1]['t1'] = round(x['t0'], 3)
        tipo = x.get('tipo') if x.get('tipo') in TIPOS - {'gancho'} else 'tese'
        clip = x.get('tema') if x.get('tema') in CATALOGO and os.path.isdir(f'{pj.pasta}/cl9/{x.get("tema")}') else None
        if tipo == 'instituicao' and not brasao: tipo = 'tese'
        beats.append(dict(t0=round(x['t0'], 3), t1=None, tipo=tipo, clip=clip, html=bloco_html(x.get('bloco'), x['t0'], brasao)))
    beats[-1]['t1'] = round(t_chamada, 3)
    for i, b in enumerate(beats):
        if not b.get('clip'): b.pop('clip', None)
        aj = ajustes.get(i)
        if aj == 'dividida': b['plano'] = 'dividida'
        if aj == 'sem_bloco': b['html'] = ''; b['plano'] = 'dividida'
    return beats


def montar_do_roteiro(pj, roteiro, t_chamada, semente, brasao=None, ajustes=None):
    """Roteiro → cenas.json. Devolve o S gravado."""
    beats = beats_do_roteiro(pj, roteiro, t_chamada, brasao, ajustes)
    et = _e(roteiro.get('etiqueta'), 34).upper()
    if et and len(et) > 14 and '<BR>' not in et:   # quebra a etiqueta em duas linhas parecidas
        meio = len(et) // 2; cortes = [i for i, ch in enumerate(et) if ch == ' ']
        if cortes: k = min(cortes, key=lambda i: abs(i - meio)); et = et[:k] + '<br>' + et[k + 1:]
    sticker = etiqueta(et, _e(roteiro.get('kicker_etiqueta') or 'atenção', 20).lower()) if et and not (ajustes or {}).get('sem_etiqueta') else None
    titulo = _e(roteiro.get('titulo_fim') or 'A PALAVRA DA BANCA NÃO É A ÚLTIMA', 44).upper()
    if '<BR>' not in titulo and len(titulo) > 18:
        cortes = [i for i, ch in enumerate(titulo) if ch == ' ']; meio = len(titulo) // 2
        if cortes: k = min(cortes, key=lambda i: abs(i - meio)); titulo = titulo[:k] + '<br>' + titulo[k + 1:]
    return escrever(pj, beats, semente, titulo_fim=titulo, t_clica=round(t_chamada + .2, 2), sticker=sticker, brasao=brasao)


def ajustes_por_colisao(S, colisoes, ajustes=None):
    """O que mudar quando a conferência acusa texto sobre o rosto: a etiqueta sai; o trecho em tela cheia vira tela
    dividida (o rosto vai para o cartão e o texto para o painel); se já era dividida, o bloco de texto sai."""
    aj = dict(ajustes or {})
    for c in colisoes:
        i = next((k for k, sc in enumerate(S['scenes']) if sc['t0'] <= c['t'] < sc['t1']), None)
        if i is None or S['scenes'][i]['layout'] in ('cta', 'fim'): continue
        if c.get('el') == 'sticker': aj['sem_etiqueta'] = True
        elif aj.get(i) == 'dividida' or S['scenes'][i]['layout'] == 'split': aj[i] = 'sem_bloco'
        else: aj[i] = 'dividida'
    return aj
