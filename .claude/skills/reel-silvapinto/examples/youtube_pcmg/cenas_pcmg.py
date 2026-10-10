"""Exemplo: YouTube da PCMG (09/10/2026, 7:13), com os motion graphics (brasoes, seta, barra, pessoas, mil).
PCMG no YouTube (09/10/2026): fala do app do HeyGen (look do escritório, 16:9), acelerada para 1.1x.
Parte 1 = 0 a 297,0 s ("...a Polícia Civil precisa de mais três mil policiais."). A parte 2 entra depois.
Tempos das palavras: ../transcricao_11x.json.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts", "youtube"))
from cenas import *  # noqa: E402,F401,F403

END = abrir(".")
P2 = 297.0          # onde a parte 2 entra (fala_total.mp4 = fala_p1 + parte 2 em 1.1x)
CR = json.load(open("creditos.json"))


def G(x):
    return f'<span class="g">{x}</span>'


def h(txt, t, fs=110, an="up", mt=14):
    return f'<div class="h1" style="font-size:{fs}px;margin-top:{mt}px" {a(t, an)}>{txt}</div>'


def s(txt, t, fs=38, mt=22):
    return f'<div class="sub" style="font-size:{fs}px;margin-top:{mt}px" {a(t)}>{txt}</div>'


def fonte(txt, t):
    return (f'<div style="margin-top:22px;font:500 20px \'JetBrains Mono\',monospace;color:rgba(255,255,255,.6)" '
            f'{a(t, "fade")}>{txt}</div>')


def card(t, titulo, sub="", ic=None, ouro=False, flex=1, t_sub=None):
    bola = f'<div class="bola" style="margin-bottom:22px">{{ic:{ic}}}</div>' if ic else ""
    borda = "border-color:var(--gold);" if ouro else ""
    sub_html = ""
    if sub:
        sub_html = (f'<div class="sub" style="margin-top:14px;font-size:36px" {a(t_sub, "fade")}>{sub}</div>'
                    if t_sub else f'<div class="sub" style="margin-top:14px;font-size:36px">{sub}</div>')
    return (f'<div class="card" style="flex:{flex};{borda}" {a(t)}>{bola}<div class="h3">{titulo}</div>{sub_html}</div>')


def linha(t, ic, txt, fs=36):
    return (f'<div style="display:flex;align-items:center;gap:18px;margin-top:22px;font:600 {fs}px/1.25 Manrope" {a(t, "left")}>'
            f'<span class="bola" style="width:66px;height:66px;font-size:32px">{{ic:{ic}}}</span><span>{txt}</span></div>')


QUEM = ('<div style="display:inline-block;margin-top:26px;font:700 34px Manrope;background:rgba(0,0,0,.6);'
        'padding:12px 22px;border-left:5px solid var(--gold)" {}>'
        '<small style="display:block;font:500 20px \'JetBrains Mono\';color:var(--gold);letter-spacing:.12em;'
        'text-transform:uppercase">delegada-geral da Polícia Civil de MG</small>Letícia Gamboge</div>')

def brasoes(t, alt=130, mb=18, so_pc=False):
    """O brasão da PCMG (e o da Polícia Penal, quando o arquivo existir) entrando com brilho dourado."""
    imgs = [f'<img src="img/brasao.png" style="height:{alt}px" {a(t, "glow", .6)}>']
    if not so_pc and os.path.exists("img/brasao_ppmg.png"):
        imgs.append(f'<img src="img/brasao_ppmg.png" style="height:{alt}px" {a(t + .25, "glow", .6)}>')
    return f'<div style="display:flex;gap:26px;align-items:flex-end;margin-bottom:{mb}px">{"".join(imgs)}</div>'


def seta(t, w=90):
    return (f'<svg width="{w}" height="44" viewBox="0 0 90 44" style="flex:none;overflow:visible">'
            f'<path pathLength="1" d="M4 22 H80 M64 8 L82 22 L64 36" stroke="#F0CF86" stroke-width="6" fill="none" '
            f'stroke-linecap="round" stroke-linejoin="round" {a(t, "draw", .5)}/></svg>')


def mil(t, fs=170, d=1.2):
    return f'<span class="h1 g" style="font-size:{fs}px" data-cont="0,3000" data-fmt="milhar" {a(t, "fade", d)}>3.000</span>'


def barra(t, frac, rotulo, fim, ouro=False):
    """Uma linha da linha do tempo: o rótulo, o trilho e a barra que cresce até `frac` com a data na ponta."""
    cor = "var(--gold)" if ouro else "rgba(240,207,134,.75)"
    return (f'<div style="display:flex;align-items:center;gap:30px;margin-top:34px" {a(t - .3, "fade", .3)}>'
            f'<div style="width:380px;font:600 34px/1.2 Manrope">{rotulo}</div>'
            f'<div style="flex:1;position:relative;height:56px;background:rgba(255,255,255,.08);border-radius:10px">'
            f'<div style="position:absolute;left:0;top:0;bottom:0;width:{frac * 100:.1f}%;background:{cor};border-radius:10px" '
            f'{a(t, "grow", 1.4)}></div>'
            f'<div class="h3 g" style="position:absolute;left:{frac * 100:.1f}%;top:-4px;padding-left:22px;font-size:62px;white-space:nowrap" '
            f'{a(t + 1.2, "fade", .4)}>{fim}</div></div></div>')


cenas = [
    # ── gancho
    B(0.0, 6.6,
      f'{brasoes(0.15)}'
      f'{tag("Polícia Civil e Polícia Penal · MG", 0.3)}'
      f'{h("Você é " + G("excedente") + "?", 0.9, 160)}'
      f'{s("Em concurso ainda válido", 2.7, 44)}',
      photo="formatura_corredor.jpg", kb=[1.04, 1.14, 0, -40, 0, -20], credit=CR["formatura_corredor"]),
    W(6.6, 11.0,
      f'{tag("Presta atenção", 6.8)}{h("Anúncio " + G("muito importante"), 9.0)}', nome=True),
    B(11.0, 17.75,
      f'{tag("Fez o último concurso da PC?", 11.8)}'
      f'{h("Ficou fora por " + G("poucos pontos") + "?", 14.0, 140)}'
      f'{s("E acha que esse assunto já acabou?", 16.2, 44)}',
      photo="letreiro.jpg", kb=[1.0, 1.1, 0, 0, 0, 30], credit=CR["letreiro"]),
    X(17.75, 21.85,
      f'{tag("Fica até o final", 17.8)}{h("Quero falar " + G("com você"), 19.5, 120)}'),
    W(21.85, 28.5,
      f'{tag("Nesta notícia", 21.9)}{h("Uma parte " + G("mais importante"), 24.2)}'
      f'{s("do que saber que vai haver um novo concurso", 26.3)}'),
    # ── capítulo 1: a notícia
    B(28.5, 33.2,
      f'{tag("Capítulo 1 · A notícia", 28.6)}{h(G("Duas") + " medidas", 30.2, 160, "pop")}'
      f'{s("anunciadas pelo governador na segurança pública", 31.6, 44)}',
      photo="bh_panorama.jpg", kb=[1.0, 1.08, 0, -50, 0, 0], credit=CR["bh_panorama"]),
    I(33.2, 45.6,
      f'{tag("As duas medidas", 33.3)}'
      f'<div style="display:flex;gap:40px;margin-top:40px;align-items:stretch">'
      f'<div class="card" style="flex:1" {a(33.4)}><div class="h3">1 · Novo concurso da {G("Polícia Civil")}</div>'
      f'<div style="display:flex;align-items:baseline;gap:22px;margin-top:18px">'
      f'{mil(37.9)}'
      f'<span class="sub" {a(38.2, "fade")}>vagas previstas</span></div></div>'
      f'<div class="card" style="flex:1;border-color:var(--gold)" {a(39.5)}><div class="h3">2 · Nomeação dos {G("excedentes")}</div>'
      f'<div class="sub" style="margin-top:14px;font-size:36px" {a(40.9, "fade")}>Concursos ainda válidos da Polícia Civil e da Polícia Penal</div>'
      f'<div style="margin-top:18px">{brasoes(42.6, 96, 0)}</div></div>'
      f'</div>',
      photo="formatura_aerea.jpg", credit=CR["formatura_aerea"]),
    W(45.6, 53.4,
      f'{tag("Quem olha para isso", 45.8)}{h("Dois " + G("grupos"), 46.1, 130)}'
      f'{s(G("1.") + " Aprovados, aguardando a nomeação", 48.3)}'
      f'{s(G("2.") + " Quem quer entrar na Polícia Civil", 50.8)}'),
    # ── capítulo 2: o novo concurso
    B(53.4, 60.5,
      f'{brasoes(53.5, 110, 10, so_pc=True)}{tag("Capítulo 2 · O novo concurso", 53.6)}'
      f'<div style="display:flex;align-items:baseline;gap:28px">{mil(54.2, 170, 1.0)}<span class="h1" style="font-size:150px" {a(54.6)}>vagas</span></div>'
      + QUEM.format(a(55.5)) + s("Em vídeo no perfil oficial da corporação", 58.4, 36),
      photo="del_caratinga.jpg", kb=[1.0, 1.08, 0, 0, 0, -30], credit=CR["del_caratinga"]),
    W(60.5, 66.6,
      f'{tag("Segundo a PCMG", 60.8)}{h("Concurso " + G("autorizado"), 61.7, 120)}'
      f'{s("Editais ainda em 2026", 63.0, 42)}{fonte("Fonte: @pcmg.oficial, 08/10/2026", 63.6)}'),
    I(66.6, 80.0,
      f'{tag("Atenção · ainda não se sabe", 66.9)}{h("Quantas vagas " + G("por cargo") + "?", 69.2, 120)}'
      f'<div style="display:flex;flex-wrap:wrap;gap:20px;margin:36px 0 10px">'
      f'<span class="chip" {a(71.0, "pop")}>Investigador ?</span><span class="chip" {a(72.1, "pop")}>Delegado ?</span>'
      f'<span class="chip" {a(73.0, "pop")}>Perito ?</span><span class="chip" {a(73.8, "pop")}>Médico-legista ?</span></div>'
      f'{s("Banca e cronograma: só com os atos oficiais", 76.2, 44, 30)}',
      photo="formatura_diagonal.jpg", credit=CR["formatura_diagonal"]),
    X(80.0, 86.6,
      f'{h("3 mil vagas: " + G("sim"), 82.4, 120, "pop", 0)}{h("Por cargo: " + G("ainda não"), 84.6, 120, "pop", 8)}'),
    # ── capítulo 3: os excedentes
    W(86.6, 94.4,
      f'{tag("Os excedentes", 86.9)}{s("Aprovado como excedente?", 87.6, 40)}'
      f'{s("O governador anunciou:", 91.5, 40)}{h("Excedentes " + G("serão nomeados"), 92.5, 104)}'),
    B(94.4, 104.0,
      f'{tag("Secretaria de Planejamento de MG", 95.0)}{h("Procedimentos " + G("já começaram"), 97.4, 140)}'
      f'{s("Cargos e datas: ainda não divulgados", 101.1, 44)}',
      photo="bh_noite.jpg", kb=[1.0, 1.08, 0, -40, 0, 0], credit=CR["bh_noite"]),
    X(104.0, 110.9,
      f'{h("Anúncio " + G("≠") + " nomeação", 104.2, 150, "pop", 0)}'
      f'{s("O que muda a situação do candidato é o " + G("ato formal"), 106.6, 44)}'),
    I(110.9, 117.0,
      f'{tag("O ato formal traz", 111.0)}'
      f'<div style="display:grid;grid-template-columns:1fr 1fr;column-gap:60px;margin-top:20px">'
      f'{chk(0, "Publicação no Diário Oficial", 111.0, "news")}{chk(0, "Quantitativo", 112.4, "list-check")}'
      f'{chk(0, "Cargo", 113.8, "file-text")}{chk(0, "Posição alcançada", 114.5, "route")}'
      f'{chk(0, "Convocação", 115.9, "clipboard-check")}</div>'),
    W(117.0, 127.0,
      f'{tag("Se você é excedente", 117.5)}{h("Acompanhe", 119.2, 120)}'
      f'{linha(119.5, "news", "Diário oficial")}{linha(120.8, "file-search", "Página oficial do concurso")}'
      f'{linha(122.9, "list-check", G("Até qual posição") + " as nomeações vão chegar")}'),
    I(127.0, 136.7,
      f'<div style="display:flex;gap:40px">'
      f'{card(127.2, "Não " + G("presuma"), "que a nomeação está garantida só porque houve um anúncio", ic="x")}'
      f'{card(130.8, "Não " + G("ignore"), "a notícia: ela se soma à recomposição do efetivo", ic="alert-circle", ouro=True, t_sub=133.4)}'
      f'</div>'),
    B(136.7, 142.75,
      f'{tag("Só em setembro", 137.0)}'
      f'<div style="display:flex;align-items:baseline;gap:30px;margin-top:6px">'
      f'<span class="h1 g" style="font-size:240px" data-cont="0,266" {a(139.0, "fade", 1.0)}>266</span>'
      f'<span class="h2" {a(140.6)}>novos servidores<br>na Polícia Civil</span></div>'
      f'{fonte("Fonte: Agência Minas, 21/09/2026", 141.0)}',
      photo="del_iapu.jpg", kb=[1.0, 1.08, 0, 0, 0, -20], credit=CR["del_iapu"], grad="grad-l"),
    # ── capítulo 4: quem ficou fora
    W(142.75, 147.7,
      f'{tag("Agora", 143.1)}{h("Outro " + G("grupo"), 144.1, 130)}'
      f'{s("Talvez a parte mais importante deste vídeo", 145.9)}', lado="L"),
    B(147.7, 153.35,
      f'{brasoes(147.8, 110, 10, so_pc=True)}{tag("Capítulo 4 · Quem ficou fora", 147.9)}{h("Ficou " + G("de fora") + "?", 150.5, 170, "pop")}'
      f'{s("Ou terminou mal classificado no último concurso da Polícia Civil?", 151.6, 44)}',
      photo="medalhas.jpg", kb=[1.04, 1.14, 0, 30, 0, 0], credit=CR["medalhas"]),
    W(153.35, 161.3,
      f'{tag("Muita gente pensa", 153.5)}{h("“Não tem " + G("mais o que fazer") + "”", 157.4, 104)}'
      f'{s("Isso não é necessariamente verdade.", 159.7, 40)}'),
    I(161.3, 169.75,
      f'{tag("Dois prazos diferentes", 161.5)}'
      f'<div style="display:flex;align-items:center;gap:40px;margin-top:44px">'
      f'{card(162.5, "Validade " + G("do concurso"), "o tempo para nomear os aprovados")}'
      f'<div class="h1 g" style="font-size:200px" {a(164.5, "pop")}>≠</div>'
      f'{card(165.6, "Prazo " + G("da ação"), "para questionar o ato ilegal que prejudicou você", ouro=True, t_sub=167.0)}'
      f'</div>'),
    W(169.75, 180.8,
      f'{tag("Procedimento comum", 171.4)}{s("Ações contra o Estado", 172.6, 40, 10)}'
      f'{h("Prescrição " + G("quinquenal"), 174.8, 104)}'
      f'<div style="margin-top:28px" {a(176.2, "pop")}><span class="chip" style="font-size:52px">Decreto 20.910/1932</span></div>'),
    I(180.8, 189.1,
      f'{tag("Em regra", 182.3)}'
      f'<div style="display:flex;align-items:baseline;gap:34px">'
      f'<span class="h1 g" style="font-size:320px" data-cont="0,5" {a(184.5, "fade", .6)}>5</span>'
      f'<span class="h1" style="font-size:180px" {a(184.8)}>anos</span></div>'
      f'{s("contados do ato ou fato que gerou a lesão discutida", 185.4, 48)}'
      f'<div style="display:flex;gap:14px;margin-top:40px">'
      + "".join(f'<div style="flex:1;height:22px;background:var(--gold);border-radius:6px;opacity:{.45 + .11 * k}" '
                f'{a(185.6 + .28 * k, "grow", .35)}></div>' for k in range(5))
      + '</div><div style="display:flex;justify-content:space-between;margin-top:12px;font:500 26px \'JetBrains Mono\';color:rgba(255,255,255,.7)">'
      + "".join(f'<span {a(185.6 + .28 * k, "fade", .3)}>ano {k + 1}</span>' for k in range(5)) + '</div>'),
    W(189.1, 201.0,
      f'{tag("Validade encerrada?", 190.6)}{h("A chance " + G("não some"), 193.0, 120)}'
      f'{s("de questionar na Justiça uma ilegalidade ocorrida na prova", 197.6)}', lado="L"),
    I(201.0, 215.0,
      f'{tag("Último concurso da PCMG", 201.2)}{h("A validade " + G("nem acabou"), 203.2, 130)}'
      f'<div style="position:relative;height:30px;margin:34px 0 0 410px;font:500 24px \'JetBrains Mono\';color:rgba(255,255,255,.6)" {a(204.6, "fade")}>'
      f'<span style="position:absolute;left:0">hoje</span><span style="position:absolute;left:{3 / 26 * 100:.1f}%">2027</span>'
      f'<span style="position:absolute;left:{15 / 26 * 100:.1f}%">2028</span></div>'
      f'{barra(205.3, 14 / 26, "Investigador, perito e médico-legista", "dez/2027")}'
      f'{barra(211.4, 19 / 26, "Delegado", "mai/2028", ouro=True)}'
      f'<div style="margin-top:40px" {a(213.7, "pop")}><span class="chip cheio" style="font-size:52px">{{ic:hourglass}} E pode ser prorrogada</span></div>',
      credit="Fonte: editais do concurso (FGV/ACADEPOL), item 16.4"),
    # ── capítulo 5: a questão de prova
    W(215.0, 221.95,
      f'{tag("Imagine", 215.2)}{h("Fora por " + G("1 ou 2 questões"), 216.7, 110)}'),
    I(221.95, 230.65,
      f'{tag("E se uma delas", 222.0)}<div style="margin-top:20px">'
      f'{chk(0, "Cobrou conteúdo fora do edital", 222.2, "file-search")}'
      f'{chk(0, "Tinha um erro objetivo e evidente", 225.2, "alert-triangle")}'
      f'{chk(0, "Ou outra ilegalidade juridicamente demonstrável", 227.7, "scale")}</div>'),
    W(230.65, 240.15,
      f'{tag("Gabarito mantido?", 232.8)}{h("A ilegalidade " + G("não desaparece"), 235.7, 100)}'
      f'{s("Pode ser levada ao Judiciário pelo procedimento comum", 237.7)}', lado="L"),
    I(240.15, 247.8,
      f'{tag("Dependendo do caso, o pedido pode envolver", 240.5)}'
      f'<div style="display:flex;align-items:center;gap:30px;margin-top:50px">'
      f'<div class="card" style="flex:1;text-align:center" {a(243.2)}><div class="bola" style="margin:0 auto 18px">{{ic:x}}</div><div class="h3">Anulação da questão</div></div>'
      f'{seta(244.2)}'
      f'<div class="card" style="flex:1;text-align:center" {a(244.6)}><div class="bola" style="margin:0 auto 18px">{{ic:writing}}</div><div class="h3">Recálculo da nota</div></div>'
      f'{seta(245.8)}'
      f'<div class="card" style="flex:1;text-align:center;border-color:var(--gold)" {a(246.2)}><div class="bola" style="margin:0 auto 18px">{{ic:list-check}}</div><div class="h3">Reclassificação</div></div></div>'),
    W(247.8, 257.7,
      f'{tag("Com os novos pontos", 248.4)}{h("A sua posição " + G("mudou") + "?", 250.0, 110)}'
      f'{s("É possível pedir os efeitos da nova classificação", 254.7)}'),
    I(257.7, 268.1,
      f'{tag("Conforme o estágio do certame e o caso concreto", 257.8)}<div style="margin-top:6px">'
      f'{chk(1, "Questão ilegal", 257.9)}{chk(2, "Anulação", 258.3)}{chk(3, "Recálculo", 258.7)}'
      f'{chk(4, "Reclassificação", 259.1)}{chk(5, G("Possível reintegração") + " ao concurso", 263.1)}</div>',
      photo="formatura_corredor.jpg", credit=CR["formatura_corredor"]),
    X(268.1, 271.45, f'{h("Não é anular " + G("por anular"), 268.6, 130, "pop", 0)}'),
    W(271.45, 277.6,
      f'{tag("O ponto central", 271.9)}{h("Consequência " + G("real"), 275.1, 110)}'
      f'{s("na sua classificação", 276.5, 40)}'),
    # ── as 3 mil vagas para quem ficou fora
    B(277.6, 284.6,
      f'{tag("De volta às 3 mil vagas", 278.3)}{h("Merece a atenção de " + G("quem fez o último concurso"), 281.0, 120)}',
      photo="formatura_aerea.jpg", kb=[1.0, 1.1, 0, -40, 0, 0], credit=CR["formatura_aerea"]),
    W(284.6, 290.65,
      f'{tag("Novo concurso", 284.9)}{h("Não cria direito " + G("automático"), 287.4, 104)}'
      f'{s("para quem ficou fora do anterior", 288.9)}', lado="L"),
    B(290.65, P2,
      f'{tag("Mas é um dado relevante", 291.0)}{h("A PC precisa de " + G("mais 3 mil policiais"), 294.5, 130)}',
      photo="del_ipatinga.jpg", kb=[1.0, 1.08, 0, 0, 0, -20], credit=CR["del_ipatinga"]),
]


def pessoas(t_ouro, t_cinza, n_ouro=1, n=7, fs=140):
    """Uma fila de candidatos: os primeiros em dourado (quem entrou com a ação), os outros apagados."""
    out = []
    for k in range(n):
        if k < n_ouro:
            out.append(f'<span class="ic g" {a(t_ouro + .2 * k, "glow", .5)}>{{ic:user-filled}}</span>')
        else:
            out.append(f'<span class="ic" style="color:rgba(255,255,255,.3)" {a(t_cinza + .12 * k, "pop", .35)}>{{ic:user-filled}}</span>')
    return f'<div style="display:flex;gap:24px;font-size:{fs}px;margin:30px 0">{"".join(out)}</div>'


def caixa(t, ic, txt, ouro=False):
    borda = "border-color:var(--gold);" if ouro else ""
    an = "glow" if ouro else "up"
    return (f'<div class="card" style="flex:1;text-align:center;padding:30px 18px;{borda}" {a(t, an)}>'
            f'<div class="bola" style="margin:0 auto 16px">{{ic:{ic}}}</div><div class="h3" style="font-size:52px">{txt}</div></div>')


PARTE2 = [
    W(P2, P2 + 8.2,
      f'{tag("Para quem ficou fora", P2 + .2)}{h("Vale verificar " + G("agora"), P2 + 4.6, 112)}'
      f'{s("se aquela pontuação mudaria a sua classificação", P2 + 6.2)}'),
    X(P2 + 8.2, P2 + 14.5,
      f'{tag("Você pode estar pensando", P2 + 9.3)}{h("“A minha prova " + G("não foi agora") + "”", P2 + 12.0, 120)}'
      f'{s("Já passou muito tempo?", P2 + 13.6, 44)}'),
    I(P2 + 14.5, P2 + 26.6,
      f'{tag("De onde o prazo conta", P2 + 15.3)}{h("Não conclua que " + G("perdeu o prazo"), P2 + 19.7, 110)}'
      f'{barra(P2 + 17.6, .42, "Fim da validade", "não é o marco")}'
      f'{barra(P2 + 21.6, .66, "Prazo da ação", "do ato lesivo", ouro=True)}'
      f'{s("dentro da ação cabível", P2 + 25.8, 40, 30)}'),
    W(P2 + 26.6, P2 + 36.6,
      f'{tag("Concurso encerrado?", P2 + 28.5)}{h("Pode estar " + G("dentro do prazo"), P2 + 32.6, 110)}'
      f'{s("para levar a ilegalidade à Justiça", P2 + 34.3)}', lado="L"),
    X(P2 + 36.6, P2 + 39.0, f'{h("Outro detalhe " + G("importante"), P2 + 37.6, 130, "pop", 0)}'),
    I(P2 + 39.0, P2 + 55.4,
      f'{tag("Ação individual de outro candidato", P2 + 39.3)}'
      f'{pessoas(P2 + 39.6, P2 + 45.3)}'
      f'{h("Os pontos " + G("não vão para todos"), P2 + 47.6, 120)}'
      f'{s("Em regra, a decisão vale para quem participa daquela ação", P2 + 51.6, 44)}',
      credit="Ver STJ, AgInt no RMS 74.847/RJ"),
    W(P2 + 55.4, P2 + 62.3,
      f'{tag("Esperar o outro?", P2 + 56.9)}{h("Não resolve " + G("o seu caso"), P2 + 60.6, 110)}'),
    I(P2 + 62.3, P2 + 69.2,
      f'{tag("Na mesma situação?", P2 + 63.4)}'
      f'{pessoas(P2 + 62.6, P2 + 62.9, n_ouro=2)}'
      f'{h("Com a " + G("sua própria ação"), P2 + 67.6, 120)}'
      f'{s("pode ser possível buscar o mesmo resultado", P2 + 65.4, 44)}'),
    W(P2 + 69.2, P2 + 74.2,
      f'{tag("Silva Pinto Advocacia", P2 + 69.6)}{h("Onde entra " + G("o nosso trabalho"), P2 + 70.6, 110)}', nome=True),
    I(P2 + 74.2, P2 + 87.0,
      f'{tag("O que fazemos na análise", P2 + 74.3)}<div style="margin-top:16px">'
      f'{chk(1, "Analisamos a sua prova", P2 + 74.6)}'
      f'{chk(2, "Identificamos questões com ilegalidade juridicamente defensável", P2 + 76.6)}'
      f'{chk(3, "Verificamos quantos pontos você perdeu", P2 + 80.9)}'
      f'{chk(4, G("Simulamos a classificação") + " que você teria com esses pontos", P2 + 83.3)}</div>'),
    I(P2 + 87.0, P2 + 104.2,
      f'{tag("Se houver fundamento e prazo", P2 + 87.3)}{s("Ação pelo procedimento comum para buscar:", P2 + 92.5, 44, 4)}'
      f'<div style="display:flex;align-items:center;gap:14px;margin-top:44px">'
      f'{caixa(P2 + 95.3, "x", "Anulação")}{seta(P2 + 96.6, 60)}{caixa(P2 + 97.3, "writing", "Recálculo")}{seta(P2 + 98.4, 60)}'
      f'{caixa(P2 + 98.9, "list-check", "Reclassificação")}{seta(P2 + 101.6, 60)}{caixa(P2 + 102.5, "route", "Reintegração", ouro=True)}</div>'
      f'{s("quando juridicamente cabível", P2 + 102.9, 36, 26)}'),
    B(P2 + 104.2, P2 + 107.3,
      f'{brasoes(P2 + 104.4, 110, 10)}{tag("Resultados do escritório", P2 + 104.6)}'
      f'{h(G("Vários clientes") + " retornaram ao certame", P2 + 105.0, 130)}',
      photo="formatura_corredor.jpg", kb=[1.08, 1.16, 0, -30, 0, -10], credit=CR["formatura_corredor"]),
    I(P2 + 107.3, P2 + 113.6,
      f'{tag("A análise é individual", P2 + 107.5)}{tag("Então, guarda isso", P2 + 109.7)}'
      f'<div style="display:flex;align-items:center;gap:40px;margin-top:30px">'
      f'<div class="h1" style="font-size:140px" {a(P2 + 111.0)}>Validade do concurso</div>'
      f'<div class="h1 g" style="font-size:200px" {a(P2 + 112.0, "pop")}>≠</div></div>'
      f'<div class="h1 g" style="font-size:160px" {a(P2 + 112.6, "pop")}>Prazo da ação</div>'),
    B(P2 + 113.6, P2 + 126.8,
      f'{brasoes(P2 + 115.2, 120, 14)}{tag("Último concurso da PC ou da Polícia Penal de MG", P2 + 114.4)}'
      f'{h("Ficou fora por " + G("poucos pontos") + "?", P2 + 117.8, 140)}'
      f'{s("Veja se alguma questão pode mudar a sua classificação", P2 + 120.4, 44)}'
      f'<div style="margin-top:30px" {a(P2 + 123.5, "pop")}><span class="chip cheio" style="font-size:56px">{{ic:brand-whatsapp}} Contato na descrição</span></div>',
      photo="formatura_diagonal.jpg", kb=[1.02, 1.12, 0, -40, 0, 0], credit=CR["formatura_diagonal"], grad="grad-l"),
    W(P2 + 126.8, END,
      f'{tag("Envie para análise", P2 + 127.2)}'
      f'{linha(P2 + 127.9, "file-text", "A sua prova")}{linha(P2 + 129.0, "list-check", "A sua nota")}'
      f'{linha(P2 + 130.0, "route", "A sua classificação")}', nome=True),
]

gravar(cenas + PARTE2, com_final=True)
