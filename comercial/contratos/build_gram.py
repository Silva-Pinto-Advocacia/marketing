# -*- coding: utf-8 -*-
"""Contrato de honorários — IR sobre a GRAM (PMERJ / CBMERJ).

Mesma máquina de build_contratos.py: parte do papel timbrado original e troca
apenas os parágrafos de cláusula, preservando cabeçalho, capa, estilos, fonte,
margens, ornamentos e tabela de assinaturas.
"""
import copy, os, shutil, zipfile
from xml.etree import ElementTree as ET

SRC = "/root/.claude/uploads/a501470a-fa38-5bf1-bd0b-4b69190a97bf/e91dc042-Contrato_de_Honor_rios_PMERJ.docx"
BASE = "orig"
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
for _p, _u in NS.items():
    ET.register_namespace(_p, _u)


BLOCOS = [
    # ------------------------------------------------------------- 1 objeto
    ("T", "1 | Objeto"),
    ("S", "O que você está contratando"),
    ("P", [("PROPOSITURA E ACOMPANHAMENTO DE AÇÃO JUDICIAL DE NATUREZA TRIBUTÁRIA EM FACE DO ESTADO "
            "DO RIO DE JANEIRO, PARA DISCUTIR A INCIDÊNCIA DE IMPOSTO DE RENDA SOBRE A GRATIFICAÇÃO "
            "DE RISCO DA ATIVIDADE MILITAR (GRAM), COM PEDIDO DE SUSPENSÃO OU CESSAÇÃO DA RETENÇÃO, "
            "QUANDO CABÍVEL, E RESTITUIÇÃO DOS VALORES RETIDOS NO PERÍODO NÃO PRESCRITO.", 0)]),

    # -------------------------------------------------------- 2 o que inclui
    ("T", "2 | O que está incluído"),
    ("S", "Até onde vai o nosso trabalho"),
    ("P", [("O trabalho contratado compreende:", 0)]),
    ("L", "a análise dos contracheques e da documentação fiscal, a apuração do período não prescrito e a elaboração da tese;"),
    ("L", "a propositura da ação, com pedido de tutela de urgência para suspender ou fazer cessar a retenção;"),
    ("L", "o acompanhamento do processo até o trânsito em julgado, em todas as instâncias, inclusive nos Tribunais Superiores (STJ e STF), com a interposição dos recursos cabíveis;"),
    ("L", "a fase de cumprimento de sentença ou execução, incluindo a habilitação e o levantamento do crédito por alvará, RPV ou precatório;"),
    ("L", "a comunicação ao contratante das movimentações relevantes do processo."),

    # ---------------------------------------------------- 3 o que não inclui
    ("T", "3 | O que não está incluído"),
    ("S", "O que fica de fora"),
    ("L", "a discussão de outras verbas, gratificações ou descontos, ainda que constem do mesmo contracheque;"),
    ("L", "ações relativas a outro tributo ou em face de outro ente federativo;"),
    ("L", "a retificação da declaração de ajuste anual do imposto de renda e qualquer providência perante a Receita Federal;"),
    ("L", "requerimentos administrativos perante o Estado do Rio de Janeiro ou perante a administração militar;"),
    ("L", "ações previdenciárias, disciplinares, funcionais ou de qualquer outra natureza, que dependem de contratação própria;"),
    ("L", "custas judiciais, taxas, honorários periciais e contábeis, na forma da cláusula 5."),

    # ------------------------------------------------------------- 4 preço
    ("T", "4 | Preço"),
    ("S", "Quanto você vai pagar"),
    ("P", [("Os honorários advocatícios são ajustados conforme a modalidade escolhida pelo CONTRATANTE:", 0)]),
    ("P", [("1. ", 1), ("Não haverá honorário inicial ou valor de entrada para o ajuizamento da ação.", 0)]),
    ("P", [("2. ", 1), ("Se for concedida e efetivamente implementada decisão judicial suspendendo a "
                        "retenção do IR sobre a GRAM, o CONTRATANTE pagará mensalmente ao CONTRATADO, "
                        "enquanto perdurar a suspensão, valor equivalente ao IR que deixar de ser retido "
                        "em cada competência, conforme o contracheque.", 0)]),
    ("P", [("3. ", 1), ("A mensalidade acompanhará eventual variação do desconto efetivamente suspenso e "
                        "deixará de ser devida quando a retenção for restabelecida ou quando o processo "
                        "for definitivamente encerrado, o que ocorrer primeiro.", 0)]),
    ("P", [("4. ", 1), ("Havendo recuperação de valores, serão devidos honorários de êxito de 30% (trinta "
                        "por cento) sobre o valor efetivamente recebido a título de restituição do IR "
                        "sobre a GRAM, incluídos os acréscimos que integrem o crédito. O pagamento será "
                        "devido quando o crédito for disponibilizado ao CONTRATANTE por alvará, RPV, "
                        "precatório, acordo ou outro meio.", 0)]),
    ("P", [("5. ", 1), ("Não havendo recuperação de valores, não haverá honorários de êxito. As "
                        "mensalidades vencidas enquanto a suspensão judicial produzir efeitos remuneram "
                        "os serviços prestados e não se confundem com o êxito.", 0)]),
    ("P", [("6. ", 1), ("Não há garantia de tutela de urgência, resultado, prazo ou valor. Se a suspensão "
                        "do desconto for revogada, o Estado poderá restabelecer a retenção e, conforme a "
                        "decisão aplicável, exigir os valores que entender devidos.", 0)]),
    ("P", [("7. ", 1), ("Eventual condenação em honorários de sucumbência pertence ao advogado e não "
                        "prejudica nem compensa os honorários contratados, nos termos do art. 23 da Lei "
                        "nº 8.906/1994.", 0)]),
    ("P", [("Os honorários contratados, somados aos de sucumbência, não excederão as vantagens obtidas "
            "pelo contratante, na forma do art. 38 do Código de Ética e Disciplina da OAB.", 0)]),

    # ------------------------------------------------------------- 5 custas
    ("T", "5 | Custas e despesas do processo"),
    ("S", "Quem paga o quê"),
    ("P", [("As custas judiciais, taxas, despesas de cartório, honorários periciais e contábeis e "
            "honorários de advogados correspondentes correm por conta do contratante e não estão "
            "incluídas nos honorários.", 0)]),
    ("P", [("Havendo elementos, o contratado requererá a gratuidade da justiça. Indeferido o pedido, as "
            "custas permanecem a cargo do contratante.", 0)]),
    ("P", [("Sendo o contratante vencido, os honorários de sucumbência devidos à parte contrária são de "
            "sua responsabilidade.", 0)]),

    # ---------------------------------------------------------- 6 resultado
    ("T", "6 | Resultado"),
    ("S", "O que a gente garante e o que não garante"),
    ("P", [("O contratado obriga-se a empregar sua melhor técnica e diligência na defesa dos interesses "
            "do contratante. ", 0), ("A obrigação assumida é de meio, e não de resultado.", 1)]),
    ("P", [("O contratado ", 0), ("não garante", 1),
           (", e não pode garantir, a concessão da tutela de urgência, a procedência da ação, o prazo de "
            "tramitação, o valor a ser restituído ou a data do efetivo recebimento. O resultado depende "
            "de decisão do Poder Judiciário, sobre a qual o contratado não tem controle.", 0)]),
    ("P", [("O contratante declara estar ciente, de forma expressa, de que ", 0),
           ("a suspensão da retenção é provisória enquanto não houver decisão definitiva", 1),
           (". Revogada ou reformada a decisão, o Estado poderá restabelecer o desconto e cobrar os "
            "valores que deixaram de ser retidos, com os acréscimos legais cabíveis. Nessa hipótese, as "
            "mensalidades já pagas ao contratado não são restituídas, por remunerarem serviços "
            "efetivamente prestados no período em que a suspensão produziu efeitos.", 0)]),

    # ---------------------------------------------------- 7 obrig contratado
    ("T", "7 | Obrigações do contratado"),
    ("S", "Quais são os meus deveres?"),
    ("P", [("Prestação dos serviços necessários à consecução do objeto, incluindo formulação das peças "
            "processuais e comparecimento a audiências e demais atos judiciais, em todas as instâncias, "
            "bem como a informação ao contratante das movimentações relevantes do processo.", 0)]),
    ("P", [("Prestar contas dos valores levantados em nome do contratante, repassando-lhe o saldo no "
            "prazo de 5 (cinco) dias úteis contados da compensação, deduzidos os honorários de êxito "
            "previstos na cláusula 4.", 0)]),
    ("P", [("O contratado poderá substabelecer, com ou sem reservas, a advogados correspondentes, quando "
            "o ato exigir atuação em outra comarca.", 0)]),

    # --------------------------------------------------- 8 obrig contratante
    ("T", "8 | Obrigações do contratante"),
    ("S", "Quais são os seus deveres?"),
    ("P", [("Fornecer os documentos indispensáveis para a instrução do processo e demais informações "
            "necessárias ao andamento processual, além de:", 0)]),
    ("L", "Encaminhar os contracheques e as declarações de imposto de renda do período discutido;"),
    ("L", "Enviar mensalmente o contracheque enquanto perdurar a suspensão, para a apuração do honorário mensal previsto na cláusula 4; não havendo envio, a mensalidade será apurada pelo último contracheque disponível;"),
    ("L", "Informar imediatamente o restabelecimento da retenção, bem como qualquer alteração de lotação, passagem à inatividade, transferência, exoneração ou mudança na composição da remuneração;"),
    ("L", "Comunicar ao contratado, de imediato, o recebimento de qualquer valor relacionado ao objeto deste contrato;"),
    ("L", "Manter os dados pessoais atualizados, tendo a obrigação de informar imediatamente toda e qualquer alteração de endereço, telefone ou e-mail;"),
    ("L", "Comparecer em todas as audiências ou atos processuais que exijam a sua presença."),

    # ------------------------------------------------------------- 9 prazo
    ("T", "9 | Prazo"),
    ("S", "Da duração do contrato"),
    ("P", [("É indeterminado o prazo de duração deste contrato, que tem início a partir da sua assinatura "
            "pelas partes e fica subordinado à conclusão dos serviços contratados, após o trânsito em "
            "julgado e o efetivo levantamento dos valores eventualmente reconhecidos.", 0)]),

    # --------------------------------------------------------- 10 rescisão
    ("T", "10 | Se você quiser cancelar"),
    ("S", "O que acontece"),
    ("P", [("Em caso de rescisão unilateral e injustificada do contrato por parte do contratante:", 0)]),
    ("L", "antes do ajuizamento da ação: nada será devido ao contratado;"),
    ("L", "depois do ajuizamento e antes de decisão que suspenda a retenção: serão devidos honorários arbitrados proporcionalmente ao trabalho já executado;"),
    ("L", "estando em vigor a suspensão da retenção: serão devidas as mensalidades vencidas até a data da rescisão;"),
    ("L", "havendo decisão favorável, ainda que o crédito não tenha sido recebido: serão devidos os honorários de êxito previstos na cláusula 4, exigíveis quando o crédito for disponibilizado."),
    ("P", [("A desistência da ação por vontade do contratante produz os mesmos efeitos da rescisão.", 0)]),

    # ------------------------------------------------------------ 11 lgpd
    ("T", "11 | Dados pessoais"),
    ("S", "Como a gente cuida das suas informações"),
    ("P", [("O contratado tratará os dados pessoais e os dados fiscais do contratante exclusivamente para "
            "a execução deste contrato e para o cumprimento de obrigações legais, na forma da Lei nº "
            "13.709/2018, adotando medidas de segurança adequadas e conservando-os pelo prazo exigido "
            "pela legislação.", 0)]),

    # ------------------------------------------------------- 12 assinatura
    ("T", "12 | Assinatura eletrônica"),
    ("S", "Como este contrato é assinado"),
    ("P", [("As partes reconhecem a validade da assinatura eletrônica deste contrato, na forma da Medida "
            "Provisória nº 2.200-2/2001 e da Lei nº 14.063/2020, dispensada a assinatura física.", 0)]),

    # ------------------------------------------------------------- 13 foro
    ("T", "13 | Foro"),
    ("S", "Em caso de divergência, onde será o juízo competente para decidir"),
    ("P", [("Elegem os contratantes o foro do Rio de Janeiro/RJ para dirimir quaisquer dúvidas e "
            "pendências decorrentes deste Contrato, inclusive eventual execução, ressalvada ao "
            "contratante a faculdade de ajuizar a demanda no foro de seu domicílio.", 0)]),
]


def monta(tpl, segmentos):
    p = copy.deepcopy(tpl)
    runs = p.findall(W + "r")
    if not runs:
        return p
    modelo = copy.deepcopy(runs[0])
    for filho in list(modelo):
        if filho.tag != W + "rPr":
            modelo.remove(filho)
    for r in runs:
        p.remove(r)
    for txt, negrito in segmentos:
        r = copy.deepcopy(modelo)
        rpr = r.find(W + "rPr")
        if rpr is None:
            rpr = ET.Element(W + "rPr"); r.insert(0, rpr)
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


def gera(destino):
    tree = ET.parse(os.path.join(BASE, "word/document.xml"))
    body = tree.getroot().find(W + "body")
    filhos = list(body)
    tpl = {"T": filhos[2], "S": filhos[3], "P": filhos[4], "L": filhos[18]}
    ornamentos = [copy.deepcopy(r) for r in filhos[15].findall(W + "r")
                  if r.find(".//" + W + "drawing") is not None
                  or r.find(".//{http://schemas.openxmlformats.org/markup-compatibility/2006}AlternateContent") is not None]

    novos = [monta(tpl[t], c if isinstance(c, list) else [(c, 0)]) for t, c in BLOCOS]
    for i, (t, c) in enumerate(BLOCOS):
        if t == "T" and isinstance(c, str) and "Obrigações do contratante" in c:
            for orn in reversed(ornamentos):
                novos[i].insert(1, copy.deepcopy(orn))
            break

    for el in filhos[2:30]:
        body.remove(el)
    for i, p in enumerate(novos):
        body.insert(2 + i, p)

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


n = gera("Contrato_Honorarios_GRAM.docx")
print(f"Contrato_Honorarios_GRAM.docx: {n} parágrafos, {os.path.getsize('Contrato_Honorarios_GRAM.docx')} bytes")
