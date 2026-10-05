"""Exemplo: o vídeo aprovado da PMERJ 2014 (YouTube, 3 min 23 s, 04/10/2026), escrito com cenas.py.

Rode dentro da pasta do projeto (fr/, rosto.json, img/, clips/ prontos):
    python cenas_pmerj2014.py && python ../scripts/youtube/render_youtube.py . fala.mp4
As fotos e vídeos de apoio vêm do Wikimedia Commons (busca_commons.py), com os créditos abaixo.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts", "youtube"))
from cenas import *  # noqa: E402,F401,F403

END = abrir(".")
SR = json.load(open("img/sepm_rects_px.json"))      # onde estão as frases marcadas no print do comunicado
from PIL import Image  # noqa: E402
sepm_w, sepm_h = Image.open("img/sepm_art.png").size

CR_GOV = "Foto: Carlos Magno / Governo do RJ · CC BY 2.0 BR"
CR = {
    "multidao": "Vídeo: Prefeitura de Santos · CC BY 3.0", "listas": "Vídeo: Prefeitura de Santos · CC BY 3.0",
    "listas2": "Vídeo: Prefeitura de Santos · CC BY 3.0", "portao": "Vídeo: Prefeitura de Santos · CC BY 3.0",
    "livro": "Vídeo: CanalGov · CC BY 3.0", "caneta": "Vídeo: CanalGov · CC BY 3.0",
    "tjrj": "Vídeo: STJ · CC BY 3.0", "forum": "Vídeo: STJ · CC BY 3.0", "sessao": "Vídeo: STJ · CC BY 3.0",
    "alerj": "Vídeo: TV Alerj · CC BY 3.0",
}

DOC = dict(img="anexo_doc3x.png", w=2466, h=4035)
cenas = [
    # ── abertura
    B(0.0, 4.35,
      f'<img src="img/brasao.png" style="height:150px;margin-bottom:22px" {a(0.15, "pop", .5)}>'
      f'{tag("Polícia Militar do Rio de Janeiro", 0.3)}'
      f'<div class="h1" style="font-size:150px;margin-top:14px" {a(0.6)}>Concurso de <span class="g">soldados</span></div>'
      f'<div class="h1 g" style="font-size:190px" {a(2.9, "pop", .5)}>2014</div>',
      photo="viaturas_fila.jpg", kb=[1.04, 1.16, 0, -60, 0, -20], credit=CR_GOV),
    P(4.35, 8.95, "R",
      f'{tag("Ainda gerando convocações", 4.5)}'
      f'<div style="display:flex;align-items:baseline;gap:30px;margin-top:20px" {a(4.8)}>'
      f'<span class="h1" style="font-size:150px">2014</span><span class="h2 g">→</span><span class="h1 g" style="font-size:150px">2026</span></div>'
      f'<div style="display:flex;align-items:baseline;gap:24px;margin-top:10px" {a(7.3)}>'
      f'<span class="h1 g" style="font-size:230px" data-cont="0,12" {a(7.3, "fade", 1.0)}>12</span>'
      f'<span class="h2">anos depois</span></div>', nome=True),
    D(8.95, 12.95,
      f'{tag("Diário Oficial do Estado do RJ · 02/10/2026", 9.1)}',
      dict(DOC, cam=[[0, 1233, 1500, 0.40], [1.3, 1233, 240, 0.72], [2.5, 1250, 960, 0.85]],
           marcas=[dict(r=[1112, 930, 310, 56], at=11.4)]),
      credit="Fonte: DOERJ, 02/10/2026, Parte I · dados pessoais tarjados"),
    X(12.95, 20.15,
      f'<div class="tag" {a(13.3, "left")}>Atenção</div>'
      f'<div class="h1" style="font-size:140px" {a(18.6, "pop", .45)}>Não é <span class="g">automático</span></div>'),
    P(20.15, 29.30, "L",
      f'{tag("Neste vídeo", 20.4)}'
      f'<div style="margin-top:30px">{chk(1, "O que aconteceu", 21.9)}{chk(2, "O que é o TAC", 23.2)}'
      f'{chk(3, "Por que há candidatos avançando por decisões judiciais individuais", 26.6)}</div>'),
    # ── capítulo 1
    B(29.30, 35.60,
      f'{tag("Capítulo 1 · De onde veio o problema", 29.5)}'
      f'<div class="h1" style="margin-top:14px" {a(30.2)}>A prova <span class="g">objetiva</span> de 2014</div>'
      f'<div style="margin-top:22px" {a(34.2, "pop")}><span class="chip cheio">3 questões de História</span></div>',
      clips=[("multidao", 3.4), ("livro", 2.9)], credit=CR["multidao"].split(" ·")[0] + " e CanalGov · CC BY 3.0"),
    B(35.60, 40.10,
      f'{tag("Segundo o Ministério Público do RJ", 35.8)}'
      f'<div class="h1" style="margin-top:14px" {a(37.9)}>Mais de uma década <span class="g">na Justiça</span></div>',
      clips=[("sessao", 4.6)], credit=CR["sessao"]),
    P(40.10, 46.80, "R",
      f'{tag("Legalidade discutida", 40.3)}'
      f'<div class="h1" style="margin:20px 0 34px" {a(40.9)}>As questões</div>'
      f'<div style="display:flex;gap:20px">'
      f'<span class="chip" style="font-size:130px" {a(42.9, "pop")}>21</span><span class="chip" style="font-size:130px" {a(43.8, "pop")}>22</span>'
      f'<span class="chip" style="font-size:130px" {a(44.9, "pop")}>24</span></div>'
      f'<div class="h1 g" style="margin-top:34px" {a(46.1)}>da prova azul</div>'),
    I(46.80, 52.30,
      f'{tag("Mesmo concurso", 47.0)}<div class="h1" {a(47.6)}>Na Justiça, <span class="g">resultados diferentes</span></div>'
      f'<div style="display:flex;gap:40px;margin-top:40px">'
      f'<div class="card" style="flex:1;border-color:var(--gold)" {a(48.8)}><div class="h3 g">{{ic:check}} Parte conseguiu</div><div class="sub" style="margin-top:14px">decisões favoráveis na Justiça</div></div>'
      f'<div class="card" style="flex:1" {a(50.8)}><div class="h3" style="color:#ddd">{{ic:x}} Outros não</div><div class="sub" style="margin-top:14px">ficaram de fora</div></div></div>'),
    P(52.30, 58.70, "L",
      f'{tag("O resultado", 52.5)}'
      f'<div class="h1" style="margin-top:18px" {a(54.1)}>Candidatos do mesmo concurso</div>'
      f'<div class="h1 g" {a(57.1, "pop")}>tratamentos diferentes</div>'),
    # ── capítulo 2: o TAC
    B(58.70, 68.35,
      f'{tag("Capítulo 2 · O TAC", 59.0)}'
      f'<div style="display:flex;gap:18px;margin:26px 0 22px">'
      f'<span class="chip" {a(61.6, "pop")}>Ministério Público</span><span class="chip" {a(63.0, "pop")}>Estado do RJ</span>'
      f'<span class="chip" {a(64.7, "pop")}>Alerj</span></div>'
      f'<div class="h1" {a(66.2)}>Termo de <span class="g">Ajustamento de Conduta</span></div>',
      clips=[("alerj", 9.7)], credit=CR["alerj"]),
    P(68.35, 73.10, "R",
      f'<div class="bola" style="width:120px;height:120px;font-size:64px;margin-bottom:30px" {a(68.6, "pop")}>{{ic:building-bank}}</div>'
      f'{tag("Maio de 2026", 69.2)}'
      f'<div class="h1" style="margin-top:16px" {a(72.0)}>Comunicado oficial <span class="g">da PM</span></div>'),
    D(73.10, 83.00,
      f'{tag("Secretaria de Estado de Polícia Militar · 05/05/2026", 73.3)}',
      dict(img="sepm_art.png", w=sepm_w, h=sepm_h,
           cam=[[0, 815, 760, 0.62], [2.3, 815, 1265, 1.12], [7.6, 815, 1290, 1.18]],
           marcas=[dict(r=r, at=75.7) for r in SR[[k for k in SR if k.startswith("serão")][0]]]
                  + [dict(r=r, at=81.2) for r in SR[[k for k in SR if k.startswith("referente")][0]]]),
      credit="Fonte: sepm.rj.gov.br/2026/05/concurso-cfsd-2014"),
    X(83.00, 85.95, f'<div class="h1" style="font-size:140px" {a(84.4, "pop")}>Um detalhe <span class="g">importante</span></div>'),
    P(85.95, 91.40, "L",
      f'{tag("Atenção aos critérios", 86.1)}'
      f'<div class="h1" style="margin-top:18px" {a(86.6)}>O TAC tem <span class="g">critérios</span></div>'
      f'<div class="sub" style="margin-top:26px" {a(88.4)}>Não basta ter feito o concurso em 2014.</div>'),
    I(91.40, 101.70,
      f'{tag("Quem o acordo alcança · segundo o MPRJ", 91.6)}'
      f'<div style="margin-top:36px">'
      f'{chk(0, "Candidatos ligados às ações sobre as questões 21, 22 e 24", 94.2, "check")}'
      f'{chk(0, "Que preencham as condições previstas no próprio TAC", 98.4, "check")}</div>'),
    P(101.70, 107.05, "R",
      f'{tag("E outra coisa", 101.9)}'
      f'<div class="h1" style="font-size:170px;margin-top:16px" {a(103.7, "pop")}>TAC <span class="g">≠</span> nomeação</div>'
      f'<div class="sub" style="margin-top:26px" {a(104.7)}>Quem se enquadra não vira policial automaticamente.</div>'),
    I(107.05, 117.45,
      f'{tag("A previsão: retorno ao concurso", 107.3)}'
      f'<div style="display:flex;align-items:center;gap:30px;margin-top:50px">'
      f'<div class="card" style="flex:1;text-align:center" {a(108.6)}><div class="bola" style="margin:0 auto 18px">{{ic:route}}</div><div class="h3">Retorno ao concurso</div></div>'
      f'<div class="h2 g" {a(111.2, "fade")}>→</div>'
      f'<div class="card" style="flex:1;text-align:center" {a(112.2)}><div class="bola" style="margin:0 auto 18px">{{ic:writing}}</div><div class="h3">Prova de redação</div></div>'
      f'<div class="h2 g" {a(114.2, "fade")}>→</div>'
      f'<div class="card" style="flex:1;text-align:center;border-color:var(--gold)" {a(115.7)}><div class="bola" style="margin:0 auto 18px">{{ic:list-check}}</div><div class="h3">Demais etapas</div></div></div>',
      photo="viaturas_frota.jpg", kb=[1.0, 1.08, 0, 0, 0, 0], credit=CR_GOV),
    # ── capítulo 3: ações individuais
    B(117.45, 121.55,
      f'{tag("Capítulo 3 · Ao mesmo tempo", 117.6)}'
      f'<div class="h1" style="margin-top:14px" {a(119.9)}>Processos <span class="g">individuais</span></div>',
      clips=[("tjrj", 3.0), ("forum", 1.2)], credit=CR["tjrj"]),
    D(121.55, 131.95,
      f'{tag("Diário Oficial do RJ · convocações por ordem judicial", 121.7)}',
      dict(DOC, cam=[[0, 1233, 430, 0.62], [4.6, 1000, 1240, 0.92], [7.9, 1233, 1000, 0.92]],
           marcas=[dict(r=[205, 1218, 700, 52], at=127.5), dict(r=[1112, 930, 310, 56], at=130.2)]),
      credit="Fonte: DOERJ, 02/10/2026, Parte I · dados pessoais tarjados"),
    P(131.95, 141.55, "L",
      f'<div class="bola" style="width:120px;height:120px;font-size:64px;margin-bottom:30px" {a(133.2, "pop")}>{{ic:file-search}}</div>'
      f'{tag("Viu um candidato de 2014 sendo chamado?", 133.0)}'
      f'<div class="h1" style="margin-top:18px" {a(138.4)}>Olhe o <span class="g">fundamento</span> da convocação</div>'),
    I(141.55, 150.95,
      f'{tag("Decisão judicial específica", 141.8)}'
      f'<div style="display:flex;gap:26px;margin:50px 0 40px;font-size:150px">'
      f'<span class="ic g" {a(143.0, "pop")}>{{ic:user-filled}}</span>'
      + "".join(f'<span class="ic" style="color:rgba(255,255,255,.35)" {a(146.6 + i * 0.15, "pop")}>{{ic:user-filled}}</span>' for i in range(6))
      + '</div>'
      f'<div class="h1" {a(147.5)}>Não se estende <span class="g">automaticamente</span> a todos</div>'),
    X(150.95, 155.70, f'<div class="tag" {a(151.9, "left")}>Fez o concurso de 2014 e ficou de fora?</div>'),
    B(155.70, 161.15,
      f'<div class="h1" {a(156.0)}>Não compare com a convocação <span class="g">de outro candidato</span></div>'
      f'<div class="sub" style="margin-top:20px" {a(159.5)}>O seu caso pode não ser igual.</div>',
      clips=[("listas2", 3.0), ("listas", 2.8)], credit=CR["listas"]),
    # ── capítulo 4: o que fazer
    P(161.15, 175.05, "L",
      f'{tag("Capítulo 4 · O que fazer", 161.3)}'
      f'<div style="margin-top:26px">{chk(1, "Por que você foi eliminado?", 162.1)}{chk(2, "Você se enquadra nos critérios do TAC?", 165.2)}'
      f'{chk(3, "Existiu ou existe processo no seu caso?", 168.6)}{chk(4, "Qual a situação jurídica concreta hoje?", 172.2)}</div>'),
    B(175.05, 182.85,
      f'{tag("Depois de 12 anos", 175.2)}'
      f'<div style="display:flex;flex-wrap:wrap;gap:16px;margin:24px 0 20px;max-width:1500px">'
      f'<span class="chip" {a(176.7, "pop")}>Prazo</span><span class="chip" {a(177.4, "pop")}>Tipo de ação</span>'
      f'<span class="chip" {a(178.7, "pop")}>Histórico processual</span><span class="chip" {a(179.9, "pop")}>Motivo da eliminação</span></div>'
      f'<div class="h1 g" {a(181.2, "pop")}>Fazem muita diferença</div>',
      clips=[("caneta", 2.6), ("livro", 2.9), ("portao", 2.3)], credit=CR["caneta"].split(" ·")[0] + " e Prefeitura de Santos · CC BY 3.0"),
    P(182.85, 191.45, "R",
      f'{tag("Fez o concurso de 2014?", 183.0)}'
      f'<div class="h1" style="margin-top:18px" {a(185.9)}>Entenda onde o <span class="g">seu caso</span> se encaixa</div>'
      f'<div style="margin-top:34px" {a(188.3, "pop")}><span class="chip cheio" style="font-size:50px">{{ic:brand-whatsapp}} Contato na descrição</span></div>', nome=True),
    P(191.45, END, "L",
      f'{tag("Por que individual", 191.6)}'
      f'<div class="h1" style="margin-top:18px" {a(192.8)}>A análise precisa ser <span class="g">individual</span></div>'
      f'<div class="sub" style="margin-top:26px" {a(194.9)}>TAC e decisões judiciais não atingem todos os candidatos da mesma forma.</div>'),
]

gravar(cenas)
