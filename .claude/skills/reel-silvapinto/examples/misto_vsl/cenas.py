"""Exemplo do estilo misto: o reel de teste aprovado em 29/10/2026 (trechos da VSL "A palavra da banca não é a
última"). Uso: python3 cenas.py <projeto> [semente]

Cada trecho (beat) diz: onde começa e termina, o TIPO (decide os pesos do sorteio), o b-roll que combina
(`clip`, um nome de broll.json) e o HTML do texto/infográfico. O layout (ele em tela cheia, b-roll em tela
cheia ou tela dividida) é sorteado por `escrever()`; `plano='dividida'` num trecho fixa o layout à mão.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../scripts/misto'))
from misto import *  # noqa: E402,F401

pj = carregar(sys.argv[1]); T = pj.T; TR = pj.TR
SEMENTE = int(sys.argv[2]) if len(sys.argv) > 2 else 7

t_pp, t_resp = T('poucos'), T('resposta'); t_eli, t_nao = T('elimina', 8), T('não', 11.5)
t_rec, t_ha, t_em = T('reconhece', 12), T('há', 14), T('em', 16.5); t_traz, t_volta = T('trazendo', 17), T('volta', 18)
t2, t3 = T('nota', 24), T('repetição', 26); t4 = T('inaptidão', 29); t_ou = T('ou', 31.5)
t_inv, t_forma = T('inventar', 37), T('de', 40.5); t_anu, t_ileg = T('anular', 42), T('ilegal', 44)
seta = (f'<svg width="100" height="60" viewBox="0 0 90 44" style="overflow:visible;flex:none"><path pathLength="1" d="M4 22 H80 M64 8 L82 22 L64 36" '
        f'stroke="#F0CF86" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round" {a(t_traz, "draw", .5)}/></svg>')

BEATS = [
    dict(t0=0, t1=2.62, tipo='gancho', html=''),   # o gancho é ele falando; a etiqueta fica acima da cabeça
    dict(t0=2.62, t1=TR['tese'], tipo='dado', clip='gabarito', html=zona(
        f'<div class="vidro" {a(2.75)}>{kick(2.85, "resultado do candidato")}'
        f'<div style="display:flex;align-items:center;gap:20px;margin-top:18px"><span class="bola x">{{ic:x}}</span><span class="h m">ELIMINADO</span></div>'
        f'<div style="margin-top:20px" {a(t_pp)}>' + barras(t_pp, [('sua nota × nota de corte', .92, True)]).replace('class="vidro"', '') + '</div>'
        f'<div style="margin-top:18px" {a(t_resp, "stamp", .35)}><span class="carimbo" style="font-size:54px;line-height:1">RESPOSTA DA BANCA:<br>INDEFERIDO</span></div></div>')),
    dict(t0=TR['tese'], t1=TR['judiciario'], tipo='tese', clip='estudante', html=zona(
        f'{kick(TR["tese"] + .1, "a palavra da banca")}<div class="sub" style="margin-top:10px" {a(t_eli, "left")}>a que elimina, a que põe em risco os teus sonhos</div>'
        f'<div class="h ouro brilho" style="font-size:150px;margin-top:10px" {a(t_nao, "pop", .5)}>NÃO É A ÚLTIMA.</div>')),
    dict(t0=TR['judiciario'], t1=round(t_em - 0.1, 3), tipo='prova', clip='justica', html=zona(
        f'{kick(TR["judiciario"] + .15, "o Poder Judiciário")}<div class="h ouro" style="font-size:160px;margin-top:10px" {a(t_rec)}>RECONHECE</div>'
        f'<div class="sub" style="font-size:46px" {a(t_ha)}>que há, sim, {G("situações")}</div>')),
    dict(t0=round(t_em - 0.1, 3), t1=TR['situacoes'], tipo='dado', html=zona(
        f'{kick(t_em, "há situações em que o candidato")}<div style="display:flex;align-items:center;gap:20px;margin-top:22px">'
        f'<div class="vidro" style="flex:1;text-align:center;padding:26px" {a(t_em + .2, "pop")}><div class="bola x" style="margin:0 auto 14px">{{ic:x}}</div><div class="h" style="font-size:64px">ELIMINADO</div></div>{seta}'
        f'<div class="vidro" style="flex:1;text-align:center;padding:26px;border-color:var(--gold);box-shadow:0 0 70px rgba(240,207,134,.3)" {a(t_volta, "pop", .55)}>'
        f'<div class="bola" style="margin:0 auto 14px">{{ic:check}}</div><div class="h g" style="font-size:64px">PODE VOLTAR<br>AO CONCURSO</div></div></div>')),
    dict(t0=TR['situacoes'], t1=round(t2 - 0.2, 3), tipo='lista', clip='prova', html=item(0, 5, TR['situacoes'], 'file-text', f'Questão {G("ilegal")}<br>mantida no gabarito')),
    dict(t0=round(t2 - 0.2, 3), t1=round(t3 - 0.25, 3), tipo='lista', clip='lupa', html=item(1, 5, t2 - 0.2, 'writing', f'Nota {G("mal calculada")}')),
    dict(t0=round(t3 - 0.25, 3), t1=round(t4 - 0.25, 3), tipo='lista', clip='taf', html=item(2, 5, t3 - 0.25, 'hourglass', f'Repetição {G("não contada")}<br>no TAF')),
    dict(t0=round(t4 - 0.25, 3), t1=round(t_ou - 0.05, 3), tipo='lista', clip='medico', html=item(3, 5, t4 - 0.25, 'alert-circle', f'Inaptidão {G("indevida")}<br>no exame de saúde')),
    dict(t0=round(t_ou - 0.05, 3), t1=TR['honestidade'], tipo='lista', html=item(4, 5, t_ou - 0.05, 'users', f'Inaptidão {G("injusta")} na<br>heteroidentificação')),
    dict(t0=TR['honestidade'], t1=TR['ilegal'], tipo='tese', html=zona(
        f'<div class="vidro" {a(t_inv)}><div style="font:700 52px/1.2 Manrope">Nós vamos {G("inventar fundamentação")}?</div></div>'
        f'<div style="margin-top:30px;text-align:center" {a(t_forma, "stamp", .35)}><span class="carimbo" style="font-size:96px">DE FORMA ALGUMA</span></div>')),
    dict(t0=TR['ilegal'], t1=TR['chamada'], tipo='prova', clip='juiz', html=zona(
        f'{kick(TR["ilegal"] + .1, "o Poder Judiciário")}<div class="h" style="font-size:126px;margin-top:8px" {a(t_anu)}>SÓ VAI ANULAR</div>'
        f'<div class="h ouro brilho" style="font-size:146px" {a(t_ileg, "pop", .45)}>O QUE FOR ILEGAL</div>')),
]

escrever(pj, BEATS, SEMENTE, titulo_fim='A PALAVRA DA BANCA<br>NÃO É A ÚLTIMA', t_clica=T('clica'),
         sticker=etiqueta('ELIMINADO NO<br>CONCURSO?'))
