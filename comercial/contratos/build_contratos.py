# -*- coding: utf-8 -*-
"""Gera os três contratos a partir do papel timbrado original.

Preserva integralmente: cabeçalho (header1.xml com a logomarca), a capa com o
retângulo e o título, os estilos 1Ttulo/2Subttulo/3Pargrafo/4Lista, a fonte
Segoe UI, as margens, a tabela de assinaturas e os ornamentos gráficos.
Substitui apenas os parágrafos de cláusula.
"""
import copy, os, re, shutil, zipfile
from xml.etree import ElementTree as ET

SRC = "/root/.claude/uploads/a501470a-fa38-5bf1-bd0b-4b69190a97bf/e91dc042-Contrato_de_Honor_rios_PMERJ.docx"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "wps": "http://schemas.microsoft.com/office/word/2010/wordprocessingShape",
    "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
    "wp14": "http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
    "v": "urn:schemas-microsoft-com:vml",
    "wpg": "http://schemas.microsoft.com/office/word/2010/wordprocessingGroup",
    "wpi": "http://schemas.microsoft.com/office/word/2010/wordprocessingInk",
    "w10": "urn:schemas-microsoft-com:office:word",
    "o": "urn:schemas-microsoft-com:office:office",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "wne": "http://schemas.microsoft.com/office/word/2006/wordml",
    "cx": "http://schemas.microsoft.com/office/drawing/2014/chartex",
    "aink": "http://schemas.microsoft.com/office/drawing/2016/ink",
    "am3d": "http://schemas.microsoft.com/office/drawing/2017/model3d",
    "oel": "http://schemas.microsoft.com/office/2019/extlst",
    "w16cid": "http://schemas.microsoft.com/office/word/2016/wordml/cid",
    "w16se": "http://schemas.microsoft.com/office/word/2015/wordml/symex",
    "w16cex": "http://schemas.microsoft.com/office/word/2018/wordml/cex",
    "w16": "http://schemas.microsoft.com/office/word/2018/wordml",
    "w16du": "http://schemas.microsoft.com/office/word/2023/wordml/word16du",
    "w16sdtdh": "http://schemas.microsoft.com/office/word/2020/wordml/sdtdatahash",
}
for p, u in NS.items():
    ET.register_namespace(p, u)


# ------------------------------------------------------------------ conteúdo

def objeto(nivel):
    if nivel == "BASICO":
        return [
            ("T", "1 | Objeto"),
            ("S", "O que você está contratando"),
            ("P", [("Propositura de ação judicial, com pedido de tutela de urgência, para impugnar "
                    "ilegalidade com o objetivo de reverter a eliminação ou majorar a pontuação do "
                    "contratante em ", 0), ("uma fase", 1),
                   (" do concurso público de {{CONCURSO E ÓRGÃO}}, edital {{NÚMERO E ANO DO EDITAL}}.", 0)]),
            ("P", [("A fase contratada é: ", 0), ("{{FASE}}", 1), (".", 0)]),
            ("P", [("Entende-se por fase cada etapa eliminatória ou classificatória prevista no edital do certame.", 0)]),

            ("T", "2 | O que está incluído"),
            ("S", "Até onde vai o nosso trabalho"),
            ("P", [("Dentro da fase contratada, o trabalho compreende:", 0)]),
            ("L", "a análise técnica do edital, do gabarito e da prova, e a elaboração da tese;"),
            ("L", "a elaboração e o protocolo da ação, com pedido de tutela de urgência, em até 48 horas úteis contadas do recebimento de todos os documentos necessários;"),
            ("L", "o acompanhamento do processo até o trânsito em julgado, em todas as instâncias, inclusive nos Tribunais Superiores (STJ e STF), com a interposição dos recursos cabíveis."),
            ("P", [("Se o contratante for eliminado ou prejudicado em outra fase do mesmo concurso, a "
                    "atuação dependerá de novo contrato e de novos honorários.", 0)]),

            ("T", "3 | O que não está incluído"),
            ("S", "O que fica de fora"),
            ("L", "as demais fases do concurso;"),
            ("L", "o curso de formação e a ação por preterição na nomeação;"),
            ("L", "qualquer outro concurso público;"),
            ("L", "ações de natureza diversa, como indenização por danos morais ou materiais, que dependem de contratação própria;"),
            ("L", "custas judiciais, taxas, despesas de cartório e honorários periciais, na forma da cláusula 5."),
        ]
    if nivel == "BLINDADO":
        return [
            ("T", "1 | Objeto"),
            ("S", "O que você está contratando"),
            ("P", [("Propositura das ações judiciais, com pedido de tutela de urgência, necessárias a "
                    "impugnar ilegalidades com o objetivo de reverter eliminações ou majorar a pontuação "
                    "do contratante em ", 0), ("todas as fases", 1),
                   (" do concurso público de {{CONCURSO E ÓRGÃO}}, edital {{NÚMERO E ANO DO EDITAL}}, "
                    "até a homologação do resultado final do certame.", 0)]),
            ("P", [("Entende-se por fase cada etapa eliminatória ou classificatória prevista no edital do certame.", 0)]),

            ("T", "2 | O que está incluído"),
            ("S", "Até onde vai o nosso trabalho"),
            ("P", [("Em cada uma das fases do concurso indicado na cláusula 1, o trabalho compreende:", 0)]),
            ("L", "a análise técnica do edital, do ato de eliminação e das provas, e a elaboração da tese;"),
            ("L", "a elaboração e o protocolo da ação, com pedido de tutela de urgência, em até 48 horas úteis contadas do recebimento de todos os documentos necessários;"),
            ("L", "o acompanhamento de cada processo até o trânsito em julgado, em todas as instâncias, inclusive nos Tribunais Superiores (STJ e STF), com a interposição dos recursos cabíveis."),
            ("P", [("As partes reconhecem que cada fase pode exigir uma ação autônoma. Todas elas estão "
                    "abrangidas por este contrato, ", 0),
                   ("sem novo contrato e sem novos honorários", 1),
                   (", qualquer que seja o número de fases em que o contratante venha a ser eliminado ou "
                    "prejudicado dentro do certame indicado na cláusula 1.", 0)]),

            ("T", "3 | O que não está incluído"),
            ("S", "O que fica de fora"),
            ("L", "o curso de formação e a ação por preterição na nomeação;"),
            ("L", "qualquer outro concurso público, ainda que para o mesmo cargo;"),
            ("L", "ações de natureza diversa, como indenização por danos morais ou materiais, que dependem de contratação própria;"),
            ("L", "custas judiciais, taxas, despesas de cartório e honorários periciais, na forma da cláusula 5."),
        ]
    return [
        ("T", "1 | Objeto"),
        ("S", "O que você está contratando"),
        ("P", [("Propositura das ações judiciais, com pedido de tutela de urgência, necessárias a impugnar "
                "ilegalidades com o objetivo de reverter eliminações, majorar a pontuação, garantir a "
                "matrícula no curso de formação ou obter a nomeação do contratante, abrangendo:", 0)]),
        ("L", "todas as fases do concurso público de {{CONCURSO E ÓRGÃO}}, edital {{NÚMERO E ANO DO EDITAL}}, até a nomeação e a posse; e"),
        ("L", "todas as fases do próximo certame para o mesmo cargo e o mesmo órgão, assim entendido o primeiro edital publicado no prazo de 24 (vinte e quatro) meses contados da assinatura deste contrato."),
        ("P", [("Entende-se por fase cada etapa eliminatória ou classificatória prevista no edital do certame.", 0)]),

        ("T", "2 | O que está incluído"),
        ("S", "Até onde vai o nosso trabalho"),
        ("P", [("Em cada uma das fases dos certames indicados na cláusula 1, o trabalho compreende:", 0)]),
        ("L", "a análise técnica do edital, do ato de eliminação e das provas, e a elaboração da tese;"),
        ("L", "a elaboração e o protocolo da ação, com pedido de tutela de urgência, em até 24 horas úteis contadas do recebimento de todos os documentos necessários;"),
        ("L", "o acompanhamento de cada processo até o trânsito em julgado, em todas as instâncias, inclusive nos Tribunais Superiores (STJ e STF), com a interposição dos recursos cabíveis;"),
        ("L", "o acompanhamento direto pelo advogado Casil da Silva Pinto, OAB/RJ nº 189.781, com reunião estratégica a cada fase acionada."),
        ("P", [("Estão igualmente abrangidas, sem novo contrato e sem novos honorários:", 0)]),
        ("L", "a ação para impugnar eliminação ou desligamento no curso de formação;"),
        ("L", "a ação por preterição ou não nomeação dentro do prazo de validade do concurso."),
        ("P", [("As partes reconhecem que cada fase pode exigir uma ação autônoma. Todas estão abrangidas "
                "por este contrato, qualquer que seja o número de fases em que o contratante venha a ser "
                "eliminado ou prejudicado nos certames indicados na cláusula 1.", 0)]),

        ("T", "3 | O que não está incluído"),
        ("S", "O que fica de fora"),
        ("L", "concursos para cargo ou órgão diversos dos indicados na cláusula 1;"),
        ("L", "o terceiro e os demais certames, além dos dois previstos na cláusula 1;"),
        ("L", "ações de natureza diversa, como indenização por danos morais ou materiais, que dependem de contratação própria;"),
        ("L", "matéria disciplinar ou funcional posterior à posse;"),
        ("L", "custas judiciais, taxas, despesas de cartório e honorários periciais, na forma da cláusula 5."),
    ]


PRAZO_PADRAO = [
    ("T", "9 | Prazo"),
    ("S", "Da duração do contrato"),
    ("P", [("É indeterminado o prazo de duração deste contrato, que tem início a partir da sua assinatura "
            "pelas partes e fica subordinado à conclusão dos serviços contratados, após sentença judicial "
            "transitada em julgado.", 0)]),
]

PRAZO_CARREIRA = [
    ("T", "9 | Prazo"),
    ("S", "Da duração do contrato"),
    ("P", [("Este contrato tem início na data da sua assinatura e vigora até a conclusão dos serviços "
            "contratados, após o trânsito em julgado das ações propostas.", 0)]),
    ("P", [("A cobertura do segundo certame, prevista na cláusula 1, extingue-se com a publicação do "
            "edital que a acionar ou com o decurso do prazo de 24 meses contados da assinatura, o que "
            "ocorrer primeiro. Não publicado edital nesse prazo, a cobertura se extingue sem direito a "
            "restituição, uma vez que os honorários remuneram a disponibilidade do serviço durante todo "
            "o período.", 0)]),
]


def comum(prazo):
    return [
        ("T", "4 | Preço"),
        ("S", "Quanto você vai pagar"),
        ("P", [("Os honorários advocatícios são ajustados no valor de ", 0),
               ("R$ {{VALOR À VISTA}}", 1),
               (" à vista mediante {{FORMA DE PAGAMENTO}}, ou {{NÚMERO DE PARCELAS}} parcelas de "
                "R$ {{VALOR DA PARCELA}} cada, totalizando R$ {{TOTAL PARCELADO}}, com vencimento da "
                "primeira em {{DATA DO PAGAMENTO OU DA PARCELA}}.", 0)]),
        ("P", [("A diferença entre o preço à vista e o total parcelado corresponde ao custo do "
                "parcelamento no cartão de crédito, na forma da Lei nº 13.455/2017.", 0)]),
        ("P", [("Não há honorários de êxito: ", 0), ("o valor acima é o total devido ao contratado", 1), (".", 0)]),
        ("P", [("Eventual condenação em verba de sucumbência em favor do contratante não prejudica os "
                "honorários aqui contratados, na forma do art. 23 da Lei nº 8.906/1994.", 0)]),
        ("P", [("O atraso superior a 15 dias no pagamento de qualquer parcela implica o vencimento "
                "antecipado das parcelas vincendas, sem prejuízo da continuidade da representação, que só "
                "cessará mediante renúncia ao mandato com observância do art. 5º, §3º, da Lei nº 8.906/1994.", 0)]),

        ("T", "5 | Custas e despesas do processo"),
        ("S", "Quem paga o quê"),
        ("P", [("As custas judiciais, taxas, despesas de cartório, honorários periciais e de advogados "
                "correspondentes correm por conta do contratante e não estão incluídas nos honorários.", 0)]),
        ("P", [("Havendo elementos, o contratado requererá a gratuidade da justiça. Indeferido o pedido, "
                "as custas permanecem a cargo do contratante.", 0)]),
        ("P", [("Sendo o contratante vencido em ação que comporte condenação em honorários de "
                "sucumbência, esses honorários são de sua responsabilidade.", 0)]),

        ("T", "6 | Resultado"),
        ("S", "O que a gente garante e o que não garante"),
        ("P", [("O contratado obriga-se a empregar sua melhor técnica e diligência na defesa dos interesses "
                "do contratante. ", 0), ("A obrigação assumida é de meio, e não de resultado.", 1)]),
        ("P", [("O contratado ", 0), ("não garante", 1),
               (", e não pode garantir, a procedência da ação, a concessão da liminar, a anulação de "
                "questões, a aprovação, a nomeação ou a posse do contratante. O resultado depende de "
                "decisão do Poder Judiciário, sobre a qual o contratado não tem controle.", 0)]),
        ("P", [("O contratante declara ter recebido essa informação de forma clara antes da assinatura.", 0)]),

        ("T", "7 | Obrigações do contratado"),
        ("S", "Quais são os meus deveres?"),
        ("P", [("Prestação dos serviços necessários à consecução do objeto, incluindo formulação das peças "
                "processuais e comparecimento a audiências e demais atos judiciais, em todas as instâncias, "
                "bem como a informação ao contratante das movimentações relevantes do processo.", 0)]),
        ("P", [("O contratado poderá substabelecer, com ou sem reservas, a advogados correspondentes, "
                "quando o ato exigir atuação em outra comarca.", 0)]),

        ("T", "8 | Obrigações do contratante"),
        ("S", "Quais são os seus deveres?"),
        ("P", [("Fornecer os documentos indispensáveis para a instrução do processo e demais informações "
                "necessárias ao andamento processual, além de:", 0)]),
        ("L", "Manter os dados pessoais atualizados, tendo a obrigação de informar imediatamente toda e qualquer alteração de endereço, telefone ou e-mail;"),
        ("L", "Indicar, quando requisitado, testemunhas para a audiência de instrução;"),
        ("L", "Comparecer em todas as audiências ou atos processuais que exijam a sua presença;"),
        ("L", "Informar ao contratado, de imediato, qualquer comunicação recebida da banca ou do órgão realizador do concurso."),
    ] + prazo + [
        ("T", "10 | Se você quiser cancelar"),
        ("S", "O que acontece"),
        ("P", [("Em caso de rescisão unilateral e injustificada do contrato por parte do contratante:", 0)]),
        ("L", "antes do protocolo da ação: ficam retidos 30% dos honorários contratados, a título de remuneração do trabalho técnico já executado, e o saldo eventualmente pago é devolvido;"),
        ("L", "após o protocolo da ação: ficam retidos integralmente os honorários já pagos e permanecem devidas as parcelas vincendas, uma vez executado o trabalho principal objeto deste contrato."),
        ("P", [("A desistência da ação por vontade do contratante equipara-se à rescisão posterior ao "
                "protocolo.", 0)]),

        ("T", "11 | Dados pessoais"),
        ("S", "Como a gente cuida das suas informações"),
        ("P", [("O contratado tratará os dados pessoais do contratante exclusivamente para a execução deste "
                "contrato e para o cumprimento de obrigações legais, na forma da Lei nº 13.709/2018, "
                "adotando medidas de segurança adequadas e conservando-os pelo prazo exigido pela "
                "legislação.", 0)]),

        ("T", "12 | Assinatura eletrônica"),
        ("S", "Como este contrato é assinado"),
        ("P", [("As partes reconhecem a validade da assinatura eletrônica deste contrato, na forma da "
                "Medida Provisória nº 2.200-2/2001 e da Lei nº 14.063/2020, dispensada a assinatura "
                "física.", 0)]),

        ("T", "13 | Foro"),
        ("S", "Em caso de divergência, onde será o juízo competente para decidir"),
        ("P", [("Elegem os contratantes o foro do Rio de Janeiro/RJ para dirimir quaisquer dúvidas e "
                "pendências decorrentes deste Contrato, inclusive eventual execução, ressalvada ao "
                "contratante a faculdade de ajuizar a demanda no foro de seu domicílio.", 0)]),
    ]


# ------------------------------------------------------------------ máquina

def texto(el):
    return "".join(t.text or "" for t in el.iter(W + "t"))


def monta(tpl, segmentos):
    """Clona o parágrafo-modelo e escreve os segmentos, preservando pPr e rPr."""
    p = copy.deepcopy(tpl)
    runs = p.findall(W + "r")
    if not runs:
        return p
    modelo = copy.deepcopy(runs[0])
    # limpa o run-modelo: só rPr + um w:t
    for filho in list(modelo):
        if filho.tag != W + "rPr":
            modelo.remove(filho)
    for r in runs:
        p.remove(r)
    for txt, negrito in segmentos:
        r = copy.deepcopy(modelo)
        rpr = r.find(W + "rPr")
        if rpr is None:
            rpr = ET.SubElement(r, W + "rPr")
            r.remove(rpr); r.insert(0, rpr)
        for b in rpr.findall(W + "b") + rpr.findall(W + "bCs"):
            rpr.remove(b)
        if negrito:
            rpr.insert(0, ET.Element(W + "bCs"))
            rpr.insert(0, ET.Element(W + "b"))
        t = ET.SubElement(r, W + "t")
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        t.text = txt
        p.append(r)
    return p


def gera(nivel, prazo, destino):
    tree = ET.parse(os.path.join(BASE, "word/document.xml"))
    body = tree.getroot().find(W + "body")
    filhos = list(body)

    tpl = {"T": filhos[2], "S": filhos[3], "P": filhos[4], "L": filhos[18]}
    # os dois ornamentos gráficos vivem no parágrafo de título da cláusula 4 antiga
    ornamentos = [copy.deepcopy(r) for r in filhos[15].findall(W + "r")
                  if r.find(".//" + W + "drawing") is not None
                  or r.find(".//{http://schemas.openxmlformats.org/markup-compatibility/2006}AlternateContent") is not None]

    blocos = objeto(nivel) + comum(prazo)

    novos = []
    for tipo, conteudo in blocos:
        segs = conteudo if isinstance(conteudo, list) else [(conteudo, 0)]
        novos.append(monta(tpl[tipo], segs))
    # devolve os ornamentos ao título "Obrigações do contratante"
    for i, (tipo, conteudo) in enumerate(blocos):
        if tipo == "T" and isinstance(conteudo, str) and "Obrigações do contratante" in conteudo:
            for orn in reversed(ornamentos):
                novos[i].insert(1, copy.deepcopy(orn))
            break

    # troca as cláusulas (índices 3..29) pelos novos parágrafos
    for el in filhos[2:30]:
        body.remove(el)
    pos = 2
    for p in novos:
        body.insert(pos, p); pos += 1

    # testemunhas: duas linhas novas na tabela de assinaturas
    tbl = body.find(W + "tbl")
    tr0 = tbl.findall(W + "tr")[0]
    for rotulo in ("Testemunha 1", "Testemunha 2"):
        tr = copy.deepcopy(tr0)
        for t in tr.iter(W + "t"):
            if t.text == "Contratante":
                t.text = rotulo
            elif t.text == "{{NOME COMPLETO}}":
                t.text = "{{NOME}}"
            elif t.text and "{{NÚMERO DO CPF}}" in t.text:
                t.text = t.text.replace("{{NÚMERO DO CPF}}", "{{CPF}}")
        tbl.append(tr)

    shutil.copy(SRC, destino)
    xml = ET.tostring(tree.getroot(), encoding="UTF-8", xml_declaration=True).decode("utf-8")
    xml = xml.replace("<?xml version='1.0' encoding='UTF-8'?>",
                      '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n')

    zin = zipfile.ZipFile(SRC)
    zout = zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED)
    for item in zin.infolist():
        dados = xml.encode("utf-8") if item.filename == "word/document.xml" else zin.read(item.filename)
        zout.writestr(item, dados)
    zout.close(); zin.close()
    return len(novos)


BASE = "orig"
for nivel, prazo, nome in [("BASICO", PRAZO_PADRAO, "Contrato_Honorarios_BASICO.docx"),
                           ("BLINDADO", PRAZO_PADRAO, "Contrato_Honorarios_BLINDADO.docx"),
                           ("CARREIRA", PRAZO_CARREIRA, "Contrato_Honorarios_CARREIRA.docx")]:
    n = gera(nivel, prazo, nome)
    print(f"{nome}: {n} parágrafos de cláusula, {os.path.getsize(nome)} bytes")
