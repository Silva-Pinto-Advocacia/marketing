"""Sorteio de layout por trecho (planejamento do dono, 29/10/2026: "b-rolls na própria tela, alternando com o
vídeo" e "de vez em quando a tela dividida"). Cada trecho tem um TIPO; o sorteio usa pesos por tipo e só aceita
o plano que cumpre as regras. A semente fixa o resultado (o mesmo vídeo sai igual de novo)."""
import random

PESOS = {  # cheio = ele em tela cheia; broll = imagem de apoio em tela cheia; dividida = painel + cartão
    'gancho':  {'cheio': 1},
    'tese':    {'cheio': .70, 'broll': .20, 'dividida': .10},
    'dado':    {'cheio': .25, 'broll': .30, 'dividida': .45},
    'prova':   {'cheio': .15, 'broll': .75, 'dividida': .10},
    'lista':   {'cheio': .30, 'broll': .50, 'dividida': .20},
    # primeira menção ao órgão do concurso: o brasão entra grande (misto.brasao_destaque), de preferência sobre
    # imagens da própria instituição ou da carreira
    'instituicao': {'cheio': .15, 'broll': .55, 'dividida': .30},
    'chamada': {'cta': 1}, 'fim': {'fim': 1},
}
REGRAS = dict(rosto_min=.55, broll_seguidos=2, sem_rosto_max_s=6.0, blocos_divididos_max=2, dividida_max=.35)


def valido(plano, beats):
    tot = sum(b['t1'] - b['t0'] for b in beats)
    rosto = sum(b['t1'] - b['t0'] for b, l in zip(beats, plano) if l in ('cheio', 'dividida', 'cta'))
    div = sum(b['t1'] - b['t0'] for b, l in zip(beats, plano) if l == 'dividida')
    blocos = sum(1 for i, l in enumerate(plano) if l == 'dividida' and (i == 0 or plano[i - 1] != 'dividida'))
    seg, sem_rosto = 0, 0.0
    for b, l in zip(beats, plano):
        if l == 'broll':
            seg += 1; sem_rosto += b['t1'] - b['t0']
            if seg > REGRAS['broll_seguidos'] or sem_rosto > REGRAS['sem_rosto_max_s']: return False
        else: seg, sem_rosto = 0, 0.0
    return rosto / tot >= REGRAS['rosto_min'] and blocos <= REGRAS['blocos_divididos_max'] and div / tot <= REGRAS['dividida_max']


def sortear(beats, semente, tentativas=4000):
    rnd = random.Random(semente)
    for _ in range(tentativas):
        plano = []
        for b in beats:
            op = {k: v for k, v in PESOS[b['tipo']].items() if not (k == 'broll' and not b.get('clip'))}
            if b.get('plano'): op = {b['plano']: 1}          # trecho com layout fixado à mão
            plano.append(rnd.choices(list(op), weights=list(op.values()))[0])
        # evita três layouts iguais seguidos (fora gancho, chamada e fim)
        if any(plano[i] == plano[i + 1] == plano[i + 2] == 'cheio' for i in range(len(plano) - 2)): continue
        if 'dividida' not in plano: continue          # o teste pede ao menos um bloco de tela dividida
        if valido(plano, beats): return plano
    raise SystemExit('nenhum plano válido; afrouxe as regras')
