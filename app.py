"""
Silva Pinto Advocacia - Painel de Oportunidades v5
==================================================
Mudancas v4 -> v5:
- Regras ANTI-INVENCAO reforcadas no prompt (links reais, datas estritas)
- Noticias: max 7 dias / Decisoes: max 12 meses
- Parser de JSON mais robusto (Sonnet as vezes retorna texto+JSON)
- Logo PNG transparente embutido em base64
- Fundo off-white com paleta Silva Pinto
- Logging detalhado da resposta da IA quando vier vazia
"""

import os
import json
import re
import logging
import sqlite3
import threading
import traceback
from datetime import datetime, timezone, timedelta
from contextlib import contextmanager
from pathlib import Path

from flask import Flask, request, jsonify, Response
import anthropic

# Config
APP_VERSION = "v5.1-2026-05-05-janelas-ajustadas"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

log.info("=" * 70)
log.info("Silva Pinto Oportunidades %s INICIANDO", APP_VERSION)
log.info("=" * 70)

DB_PATH = Path(os.environ.get("DB_PATH", "/tmp/oportunidades.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

CRON_SECRET = os.environ.get("CRON_SECRET", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL_NAME = os.environ.get("MODEL_NAME", "claude-sonnet-4-5")
DEMO_MODE = os.environ.get("DEMO_MODE", "0") == "1"

app = Flask(__name__)


CATEGORIAS = {
    "elim_ativas": {
        "tier": 1,
        "label": "Eliminacoes ativas",
        "flag": "QUENTE",
        "queries": [
            "gabarito definitivo concurso publico {mes_ano}",
            "resultado final concurso publico eliminados {mes_ano}",
            "nota de corte concurso publico aprovados {mes_ano}",
            "FGV Cebraspe Vunesp gabarito polemica concurso {mes_ano}",
        ],
        "descricao": (
            "Detectar candidatos sendo ELIMINADOS de concursos publicos AGORA. "
            "Foco: gabaritos definitivos publicados nos ultimos 7 dias, listas de "
            "resultados eliminando candidatos, notas de corte recem-divulgadas. "
            "NAO incluir simples publicacoes de edital novo (isso e Cat 4)."
        ),
        "campos_extras": ["concurso", "banca", "fase_eliminacao", "candidatos_estimados"],
        "max_idade_dias": 7,
    },
    "taf_fases": {
        "tier": 1,
        "label": "TAF e fases pos-prova",
        "flag": "TAF/FASE",
        "queries": [
            "TAF concurso eliminados resultado {mes_ano}",
            "psicotecnico concurso inapto recurso {mes_ano}",
            "investigacao social eliminado concurso {mes_ano}",
            "convocacao TAF concurso PMERJ PRF PM PC CBMDF {mes_ano}",
        ],
        "descricao": (
            "Eliminacao em fases pos-prova: TAF, psicotecnico, investigacao social, "
            "exame medico, heteroidentificacao. Tambem incluir convocacoes recentes "
            "(ultimos 7 dias) para essas fases."
        ),
        "campos_extras": ["concurso", "fase_eliminacao", "tipo_irregularidade"],
        "max_idade_dias": 7,
    },
    "recurso_anulacao": {
        "tier": 1,
        "label": "Questoes passiveis de recurso",
        "flag": "RECURSO",
        "queries": [
            "questao anulada banca concurso {mes_ano}",
            "gabarito definitivo alterado concurso {mes_ano}",
            "recursos deferidos banca concurso {mes_ano}",
            "Estrategia Gran QConcursos questao polemica {mes_ano}",
        ],
        "descricao": (
            "Questoes polemicas de provas RECENTES - candidatas a anulacao. "
            "Foco em: questoes ja anuladas pela banca, recursos deferidos, "
            "questoes apontadas como polemicas por professores/cursinhos."
        ),
        "campos_extras": ["concurso", "banca", "questao_numero", "afetados_estimados"],
        "max_idade_dias": 7,
    },
    "radar_volume": {
        "tier": 2,
        "label": "Radar de volume - novos concursos",
        "flag": "VOLUME",
        "queries": [
            "concurso publico inscritos abertas {mes_ano}",
            "edital concurso policial militar estado {mes_ano}",
            "concurso publico FGV Cebraspe Vunesp edital aberto {mes_ano}",
            "novo edital PM PC guarda municipal {mes_ano}",
            "pciconcursos concursos abertos {mes_ano}",
        ],
        "descricao": (
            "NOVOS CONCURSOS abertos com inscricoes ainda vigentes "
            "(prova objetiva ainda NAO realizada) - editais publicados nos "
            "ultimos 12 meses. Para cada concurso INFORMAR EXPLICITAMENTE: "
            "vagas, salario inicial, banca, prazo de inscricao, "
            "data prevista da prova."
        ),
        "campos_extras": ["concurso", "cargo", "vagas", "salario", "banca", "prazo_inscricao", "data_prova"],
        "max_idade_dias": 365,
    },
    "jurisprudencia": {
        "tier": 2,
        "label": "Jurisprudencia estrategica",
        "flag": "JURISPRUDENCIA",
        "queries": [
            "STJ decisao concurso publico candidato {ano}",
            "STF sumula concurso publico eliminacao {ano}",
            "TJ liminar concurso publico candidato deferida {ano}",
            "mandado de seguranca concurso STJ {ano}",
            "TAF ilegal decisao judicial {ano}",
        ],
        "descricao": (
            "Decisoes de tribunais (STJ, STF, TJs) FAVORAVEIS aos candidatos "
            "em concursos publicos. APENAS DECISOES DOS ULTIMOS 12 MESES. "
            "Extrair tribunal, tema, numero do processo."
        ),
        "campos_extras": ["tribunal", "tema", "numero_processo", "tese"],
        "max_idade_dias": 365,
    },
    "sentimento": {
        "tier": 3,
        "label": "Sentimento do candidato",
        "flag": "VIRAL",
        "queries": [
            "fui eliminado concurso o que fazer {mes_ano}",
            "eliminado TAF injustamente concurso {mes_ano}",
            "gabarito errado concurso reclamacao candidatos {mes_ano}",
            "site:reddit.com eliminado concurso {ano}",
        ],
        "descricao": (
            "Conteudo de candidatos desabafando em redes sociais, foruns, "
            "Reddit, YouTube, Telegram - dos ultimos 45 dias. Util para hooks "
            "de Reels (citacao real entre aspas)."
        ),
        "campos_extras": ["citacao_candidato", "concurso_mencionado", "padrao_emocional"],
        "max_idade_dias": 45,
    },
    "concorrencia": {
        "tier": 3,
        "label": "Movimentos da concorrencia",
        "flag": "CONCORRENCIA",
        "queries": [
            "safeelimaadv concurso liminar {ano}",
            "queromeuconcurso concurso liminar {ano}",
            "marcuspeterson concursos recurso {ano}",
            "advogado concurso publico viral instagram {ano}",
        ],
        "descricao": (
            "Atividades recentes (ultimos 45 dias) dos 3 concorrentes diretos: "
            "Safe & Lima, Queromeuconcurso, Marcus Peterson. Detectar quando "
            "estao entrando em concursos novos ou explorando teses inovadoras."
        ),
        "campos_extras": ["escritorio_concorrente", "concurso_tema", "gap_identificado"],
        "max_idade_dias": 45,
    },
}


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS oportunidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria TEXT NOT NULL,
            tier INTEGER NOT NULL,
            flag TEXT,
            titulo TEXT NOT NULL,
            descricao TEXT,
            orgao TEXT,
            estado TEXT,
            concurso TEXT,
            cargo TEXT,
            banca TEXT,
            vagas TEXT,
            salario TEXT,
            prazo_inscricao TEXT,
            data_prova TEXT,
            fase_atual TEXT,
            data_publicacao TEXT,
            extras_json TEXT,
            link TEXT,
            relevancia INTEGER DEFAULT 5,
            etapa_concurso TEXT,
            lido INTEGER DEFAULT 0,
            arquivado INTEGER DEFAULT 0,
            data_coleta TEXT NOT NULL,
            hash_unico TEXT UNIQUE
        );
        CREATE INDEX IF NOT EXISTS idx_categoria ON oportunidades(categoria);
        CREATE INDEX IF NOT EXISTS idx_tier ON oportunidades(tier);
        CREATE INDEX IF NOT EXISTS idx_etapa ON oportunidades(etapa_concurso);
        CREATE INDEX IF NOT EXISTS idx_data ON oportunidades(data_coleta);
        CREATE INDEX IF NOT EXISTS idx_lido ON oportunidades(lido);

        CREATE TABLE IF NOT EXISTS execucoes_cron (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_execucao TEXT NOT NULL,
            tipo_run TEXT,
            categorias_processadas TEXT,
            itens_novos INTEGER DEFAULT 0,
            duracao_segundos REAL,
            sucesso INTEGER DEFAULT 1,
            erro TEXT
        );
        """)
    log.info("DB inicializado em %s", DB_PATH)


@contextmanager
def db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def hash_for_dedup(titulo, orgao=""):
    import hashlib
    base = f"{titulo.strip().lower()[:100]}|{orgao.strip().lower()[:50]}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]


def render_queries(queries_template, hoje):
    mes_ano = hoje.strftime("%B %Y").lower()
    mes_pt = {
        "january": "janeiro", "february": "fevereiro", "march": "marco",
        "april": "abril", "may": "maio", "june": "junho",
        "july": "julho", "august": "agosto", "september": "setembro",
        "october": "outubro", "november": "novembro", "december": "dezembro",
    }
    for en, pt in mes_pt.items():
        mes_ano = mes_ano.replace(en, pt)
    ano = hoje.strftime("%Y")
    return [q.replace("{mes_ano}", mes_ano).replace("{ano}", ano) for q in queries_template]


FONTES_OFICIAIS = """
FONTES PRIORITARIAS (use de preferencia):
- pciconcursos.com.br, qconcursos.com (concursos)
- estrategiaconcursos.com.br, grancursosonline.com.br (analise tecnica)
- jusbrasil.com.br, migalhas.com.br, conjur.com.br (juridico)
- stj.jus.br, stf.jus.br (sites oficiais de tribunais)
- Sites oficiais de bancas (FGV, Cebraspe, Vunesp, IDECAN, IBADE)
- Sites oficiais de orgaos (PMs, PCs, ministerios, prefeituras)

Para Tier 3 (sentimento/concorrencia): aceite reddit.com, instagram.com,
youtube.com, tiktok.com, telegram, e perfis dos escritorios concorrentes.
"""


def parse_json_robusto(raw):
    """Parser tolerante - Sonnet as vezes retorna texto+JSON misturado."""
    if not raw:
        return None
    # Remove markdown fences
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"```\s*$", "", raw, flags=re.MULTILINE)
    raw = raw.strip()

    # Tenta direto
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Procura o maior bloco JSON valido
    # Pega do primeiro { ate o ultimo } e tenta parsear pedacos
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        for try_end in (end, raw.rfind("}", start, end)):
            if try_end <= start:
                continue
            candidate = raw[start:try_end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

    # Tenta extrair so o array "itens"
    m = re.search(r'"itens"\s*:\s*\[(.*?)\]\s*}', raw, re.DOTALL)
    if m:
        try:
            return json.loads('{"itens":[' + m.group(1) + ']}')
        except json.JSONDecodeError:
            pass

    return None


def coletar_categoria(api_key, cat_id, hoje):
    cat = CATEGORIAS[cat_id]
    queries = render_queries(cat["queries"], hoje)
    descricao = cat["descricao"]
    flag = cat["flag"]
    tier = cat["tier"]
    extras = cat.get("campos_extras", [])
    max_idade = cat.get("max_idade_dias", 7)

    todos_itens = []
    erro_msg = None

    extras_json_template = ""
    if extras:
        lines = ",\n      ".join(f'"{c}": "valor real ou vazio"' for c in extras)
        extras_json_template = f",\n      {lines}"

    queries_str = "\n".join(f"  {i+1}. {q}" for i, q in enumerate(queries))

    etapa_block = ""
    if cat_id in ("elim_ativas", "taf_fases", "recurso_anulacao", "radar_volume"):
        etapa_block = """,
      "etapa_concurso": "antes_prova" se concurso ainda NAO realizou prova objetiva, "apos_prova" se prova ja foi realizada"""

    data_limite = (hoje - timedelta(days=max_idade)).strftime("%d/%m/%Y")

    prompt = f"""Voce e um pesquisador juridico do escritorio Silva Pinto Advocacia, especializado em concursos publicos.

CATEGORIA: {cat['label']} (Tier {tier})
OBJETIVO: {descricao}

== REGRAS CRITICAS - LEIA COM ATENCAO ==

1. NUNCA INVENTE conteudo. Se a busca nao retornou resultados reais, retorne {{"itens": []}}.
2. Cada item DEVE ter um LINK REAL E VERIFICAVEL retornado pela ferramenta web_search.
   Se voce nao tem o URL exato da fonte, NAO INCLUA o item.
3. NUNCA crie URLs ficticios. NUNCA escreva "https://example.com" ou similares.
4. RESTRICAO DE DATA RIGIDA: apenas conteudo publicado em {data_limite} ou DEPOIS.
   Se o conteudo nao tem data clara OU e mais antigo, NAO INCLUA.
5. Cada item deve ser INDIVIDUAL e VERIFICAVEL: titulo deve permitir busca rapida na fonte.
6. Se nada relevante for encontrado nas buscas, retorne {{"itens": []}} - isso e ACEITAVEL.
   E muito melhor retornar zero itens do que inventar.

{FONTES_OFICIAIS}

== TAREFA ==

Realize as buscas a seguir, uma por vez, usando a ferramenta web_search:
{queries_str}

Apos as buscas, analise os RESULTADOS REAIS retornados e extraia ate 8 itens relevantes
e RECENTES (publicados a partir de {data_limite}).

== FORMATO DE RESPOSTA ==

Retorne SOMENTE JSON puro, sem markdown, sem explicacoes, sem texto antes ou depois.
NAO escreva "Aqui esta o JSON:" ou frases similares. Apenas o JSON.

{{
  "itens": [
    {{
      "titulo": "Titulo objetivo (REAL, da materia/decisao)",
      "descricao": "Resumo de 2-3 frases com dados concretos da fonte real",
      "data_publicacao": "DD/MM/AAAA da publicacao da materia (OBRIGATORIO)",
      "orgao": "Orgao/instituicao (PCMG, STJ, TJ-SP, etc) ou vazio",
      "estado": "UF (MG, SP, etc) ou Brasil se nacional",
      "concurso": "Nome do concurso (PMERJ 2026, etc) ou vazio",
      "cargo": "Cargo do concurso ou vazio",
      "banca": "Banca examinadora (FGV, Cebraspe, etc) ou vazio",
      "vagas": "Numero de vagas exato ou vazio",
      "salario": "Salario inicial em R$ exato ou vazio",
      "prazo_inscricao": "Data limite de inscricao ou vazio",
      "data_prova": "Data prevista da prova ou vazio",
      "fase_atual": "Fase em que esta (gabarito definitivo, TAF, recursos, etc) ou vazio",
      "link": "URL REAL E COMPLETO da fonte (OBRIGATORIO - sem isso, NAO inclua o item)",
      "relevancia": 1-10{extras_json_template}{etapa_block}
    }}
  ]
}}

REPETINDO AS REGRAS MAIS IMPORTANTES:
- Sem link real verificavel = NAO incluir
- Sem data clara dentro do periodo (>= {data_limite}) = NAO incluir
- Sem dados extraidos da web_search = retornar []
- Inventar = pior do que retornar []"""

    try:
        log.info("[%s tier%d] iniciando %d buscas (max %d dias)", cat_id, tier, len(queries), max_idade)
        client = anthropic.Anthropic(api_key=api_key, timeout=240.0, max_retries=2)
        msg = client.messages.create(
            model=MODEL_NAME,
            max_tokens=12000,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{"role": "user", "content": prompt}],
        )

        # Coleta texto da resposta
        text_parts = []
        web_searches_used = 0
        for block in msg.content:
            btype = getattr(block, "type", "")
            if btype == "server_tool_use" and getattr(block, "name", "") == "web_search":
                web_searches_used += 1
            elif hasattr(block, "text") and block.text:
                text_parts.append(block.text)
        raw = "".join(text_parts).strip()

        log.info("[%s] web_searches: %d, resposta texto: %d chars",
                 cat_id, web_searches_used, len(raw))

        # Parse robusto
        data = parse_json_robusto(raw)
        if data is None:
            # Loga prefixo da resposta crua pra diagnostico
            log.warning("[%s] JSON nao parseado. Preview: %s", cat_id, raw[:500])
            return [], f"JSON nao parseado (resposta: {len(raw)} chars)"

        itens = data.get("itens", [])
        log.info("[%s] %d itens extraidos do JSON", cat_id, len(itens))

        if not itens:
            log.info("[%s] IA retornou lista vazia (esperado se nada relevante)", cat_id)

        for item in itens:
            if not isinstance(item, dict):
                continue
            titulo = str(item.get("titulo", "")).strip()
            link = str(item.get("link", "")).strip()

            # Validacoes anti-invencao
            if not titulo:
                log.warning("[%s] item sem titulo, ignorando", cat_id)
                continue
            if not link or not link.startswith("http"):
                log.warning("[%s] item sem link real, ignorando: %s", cat_id, titulo[:60])
                continue
            if "example.com" in link.lower() or "example.org" in link.lower():
                log.warning("[%s] link e example.com, ignorando: %s", cat_id, titulo[:60])
                continue

            # Build extras dict
            extras_dict = {}
            for campo in extras:
                v = item.get(campo)
                if v:
                    extras_dict[campo] = str(v)[:300]

            etapa = str(item.get("etapa_concurso", "")).strip().lower()
            if etapa not in ("antes_prova", "apos_prova"):
                etapa = ""

            todos_itens.append({
                "categoria": cat_id,
                "tier": tier,
                "flag": flag,
                "titulo": titulo[:300],
                "descricao": str(item.get("descricao", "")).strip()[:1200],
                "orgao": str(item.get("orgao", "")).strip()[:100],
                "estado": str(item.get("estado", "")).strip()[:30],
                "concurso": str(item.get("concurso", "")).strip()[:120],
                "cargo": str(item.get("cargo", "")).strip()[:120],
                "banca": str(item.get("banca", "")).strip()[:60],
                "vagas": str(item.get("vagas", "")).strip()[:60],
                "salario": str(item.get("salario", "")).strip()[:60],
                "prazo_inscricao": str(item.get("prazo_inscricao", "")).strip()[:60],
                "data_prova": str(item.get("data_prova", "")).strip()[:60],
                "fase_atual": str(item.get("fase_atual", "")).strip()[:120],
                "data_publicacao": str(item.get("data_publicacao", "")).strip()[:30],
                "extras_json": json.dumps(extras_dict, ensure_ascii=False) if extras_dict else "",
                "link": link[:500],
                "relevancia": int(item.get("relevancia", 5)) if str(item.get("relevancia", 5)).isdigit() else 5,
                "etapa_concurso": etapa,
            })

        log.info("[%s] %d itens validados (com link real)", cat_id, len(todos_itens))

    except Exception as e:
        log.error("[%s] erro: %s\n%s", cat_id, e, traceback.format_exc())
        erro_msg = f"{type(e).__name__}: {str(e)[:200]}"

    return todos_itens, erro_msg


def salvar_itens(itens):
    if not itens:
        return 0
    novos = 0
    agora = datetime.now(timezone.utc).isoformat()
    with db_conn() as conn:
        for item in itens:
            h = hash_for_dedup(item["titulo"], item.get("orgao", ""))
            try:
                conn.execute(
                    """INSERT INTO oportunidades
                    (categoria, tier, flag, titulo, descricao, orgao, estado,
                     concurso, cargo, banca, vagas, salario, prazo_inscricao,
                     data_prova, fase_atual, data_publicacao, extras_json,
                     link, relevancia, etapa_concurso, data_coleta, hash_unico)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (item["categoria"], item["tier"], item["flag"],
                     item["titulo"], item["descricao"], item["orgao"], item["estado"],
                     item["concurso"], item["cargo"], item["banca"], item["vagas"],
                     item["salario"], item["prazo_inscricao"], item["data_prova"],
                     item["fase_atual"], item.get("data_publicacao", ""),
                     item["extras_json"], item["link"],
                     item["relevancia"], item["etapa_concurso"], agora, h)
                )
                novos += 1
            except sqlite3.IntegrityError:
                pass
    return novos


def executar_coleta(api_key, categorias_a_rodar, tipo_run="manual"):
    inicio = datetime.now(timezone.utc)
    total_novos = 0
    erros = []

    for cat_id in categorias_a_rodar:
        if cat_id not in CATEGORIAS:
            continue
        try:
            itens, erro = coletar_categoria(api_key, cat_id, inicio)
            novos = salvar_itens(itens)
            total_novos += novos
            log.info("[%s] %d novos salvos (de %d encontrados)", cat_id, novos, len(itens))
            if erro:
                erros.append(f"{cat_id}: {erro}")
        except Exception as e:
            erros.append(f"{cat_id}: {e}")
            log.error("[%s] falha total: %s", cat_id, e)

    duracao = (datetime.now(timezone.utc) - inicio).total_seconds()
    sucesso = len(erros) == 0

    with db_conn() as conn:
        conn.execute(
            """INSERT INTO execucoes_cron
            (data_execucao, tipo_run, categorias_processadas, itens_novos, duracao_segundos, sucesso, erro)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (inicio.isoformat(), tipo_run, ",".join(categorias_a_rodar),
             total_novos, duracao, 1 if sucesso else 0,
             "; ".join(erros) if erros else None)
        )

    return {
        "tipo_run": tipo_run,
        "sucesso": sucesso,
        "categorias": categorias_a_rodar,
        "itens_novos": total_novos,
        "duracao_segundos": round(duracao, 1),
        "erros": erros,
    }


def categorias_por_tier(*tiers):
    return [cid for cid, c in CATEGORIAS.items() if c["tier"] in tiers]


# Routes
@app.route("/")
def home():
    return Response(HTML_INDEX, mimetype="text/html")


@app.route("/logo.png")
def logo_png():
    """Serve o logo PNG embutido (decode do base64)."""
    import base64
    png_bytes = base64.b64decode(LOGO_B64)
    return Response(png_bytes, mimetype="image/png", headers={
        "Cache-Control": "public, max-age=86400"
    })


@app.route("/api/oportunidades")
def api_listar():
    categoria = request.args.get("categoria", "")
    tier = request.args.get("tier", "")
    flag = request.args.get("flag", "")
    estado = request.args.get("estado", "")
    etapa = request.args.get("etapa", "")
    incluir_lidos = request.args.get("incluir_lidos", "0") == "1"
    limite = int(request.args.get("limite", 200))
    dias = int(request.args.get("dias", 30))

    where_parts = ["arquivado = 0"]
    params = []
    if not incluir_lidos:
        where_parts.append("lido = 0")
    if categoria:
        where_parts.append("categoria = ?")
        params.append(categoria)
    if tier:
        where_parts.append("tier = ?")
        params.append(int(tier))
    if flag:
        where_parts.append("flag = ?")
        params.append(flag)
    if estado:
        where_parts.append("estado = ?")
        params.append(estado)
    if etapa:
        where_parts.append("etapa_concurso = ?")
        params.append(etapa)
    if dias > 0:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=dias)).isoformat()
        where_parts.append("data_coleta >= ?")
        params.append(cutoff)

    where_sql = " AND ".join(where_parts)
    sql = f"""SELECT * FROM oportunidades
              WHERE {where_sql}
              ORDER BY tier ASC, relevancia DESC, data_coleta DESC
              LIMIT ?"""
    params.append(limite)

    with db_conn() as conn:
        rows = conn.execute(sql, params).fetchall()

    itens = []
    for r in rows:
        d = dict(r)
        if d.get("extras_json"):
            try:
                d["extras"] = json.loads(d["extras_json"])
            except:
                d["extras"] = {}
        else:
            d["extras"] = {}
        itens.append(d)

    return jsonify({"total": len(itens), "itens": itens})


@app.route("/api/oportunidades/<int:item_id>/marcar_lido", methods=["POST"])
def api_marcar_lido(item_id):
    with db_conn() as conn:
        conn.execute("UPDATE oportunidades SET lido = 1 WHERE id = ?", (item_id,))
    return jsonify({"ok": True})


@app.route("/api/oportunidades/<int:item_id>/arquivar", methods=["POST"])
def api_arquivar(item_id):
    with db_conn() as conn:
        conn.execute("UPDATE oportunidades SET arquivado = 1 WHERE id = ?", (item_id,))
    return jsonify({"ok": True})


@app.route("/api/limpar_exemplos", methods=["POST"])
def api_limpar_exemplos():
    """Apaga itens [EXEMPLO] do banco. Usado pra limpar antes da primeira coleta real."""
    with db_conn() as conn:
        conn.execute("DELETE FROM oportunidades WHERE titulo LIKE '%[EXEMPLO]%'")
        c = conn.execute("SELECT changes()").fetchone()[0]
    return jsonify({"ok": True, "removidos": c})


@app.route("/api/status")
def api_status():
    with db_conn() as conn:
        total = conn.execute("SELECT COUNT(*) AS c FROM oportunidades").fetchone()["c"]
        nao_lidos = conn.execute(
            "SELECT COUNT(*) AS c FROM oportunidades WHERE lido = 0 AND arquivado = 0"
        ).fetchone()["c"]
        ultima = conn.execute(
            "SELECT * FROM execucoes_cron ORDER BY id DESC LIMIT 1"
        ).fetchone()
        tier_counts = {}
        for t in (1, 2, 3):
            r = conn.execute(
                "SELECT COUNT(*) AS c FROM oportunidades WHERE lido = 0 AND arquivado = 0 AND tier = ?",
                (t,)
            ).fetchone()
            tier_counts[f"tier{t}"] = r["c"]

    return jsonify({
        "total": total,
        "nao_lidos": nao_lidos,
        "tier_counts": tier_counts,
        "ultima_execucao": dict(ultima) if ultima else None,
        "model": MODEL_NAME,
        "version": APP_VERSION,
    })


@app.route("/cron/tier1", methods=["GET", "POST"])
def cron_tier1():
    if CRON_SECRET:
        secret = request.args.get("secret") or request.headers.get("X-Cron-Secret")
        if secret != CRON_SECRET:
            return jsonify({"erro": "secret invalido"}), 403
    if not ANTHROPIC_API_KEY:
        return jsonify({"erro": "API key nao configurada"}), 500

    log.info("=" * 60)
    log.info("CRON TIER 1 disparado em %s", datetime.now(timezone.utc).isoformat())
    log.info("=" * 60)

    cats = categorias_por_tier(1)
    try:
        result = executar_coleta(ANTHROPIC_API_KEY, cats, tipo_run="tier1")
        return jsonify(result)
    except Exception as e:
        log.error("Cron tier1 falhou: %s", e)
        return jsonify({"erro": str(e)}), 500


@app.route("/cron/tier23", methods=["GET", "POST"])
def cron_tier23():
    if CRON_SECRET:
        secret = request.args.get("secret") or request.headers.get("X-Cron-Secret")
        if secret != CRON_SECRET:
            return jsonify({"erro": "secret invalido"}), 403
    if not ANTHROPIC_API_KEY:
        return jsonify({"erro": "API key nao configurada"}), 500

    log.info("=" * 60)
    log.info("CRON TIER 2+3 disparado em %s", datetime.now(timezone.utc).isoformat())
    log.info("=" * 60)

    cats = categorias_por_tier(2, 3)
    try:
        result = executar_coleta(ANTHROPIC_API_KEY, cats, tipo_run="tier23")
        return jsonify(result)
    except Exception as e:
        log.error("Cron tier23 falhou: %s", e)
        return jsonify({"erro": str(e)}), 500


@app.route("/cron/manual", methods=["POST"])
def cron_manual():
    if not ANTHROPIC_API_KEY:
        return jsonify({"erro": "ANTHROPIC_API_KEY nao configurada"}), 500

    tipo = request.args.get("tipo", "completo")
    if tipo == "tier1":
        cats = categorias_por_tier(1)
    elif tipo == "tier23":
        cats = categorias_por_tier(2, 3)
    else:
        cats = list(CATEGORIAS.keys())

    log.info("Disparo MANUAL pela UI: %s", cats)

    def run_collect():
        try:
            executar_coleta(ANTHROPIC_API_KEY, cats, tipo_run="manual")
        except Exception as e:
            log.error("Manual run falhou: %s", e)

    t = threading.Thread(target=run_collect, daemon=True)
    t.start()
    return jsonify({
        "ok": True,
        "categorias": cats,
        "mensagem": f"Coleta iniciada ({len(cats)} categorias). Aguarde 2-4 minutos e recarregue."
    })


@app.route("/health")
def health():
    return jsonify({"ok": True, "version": APP_VERSION})


# Init
init_db()


# Logo PNG transparente embutido (gerado a partir da logo Silva Pinto)
LOGO_B64 = "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"


# HTML embutido
HTML_INDEX = r"""<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Silva Pinto - Painel de Oportunidades</title>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=Montserrat:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      /* Paleta Silva Pinto */
      --gold: #BB904C;
      --gold-light: #D4AF7A;
      --gold-dark: #9a7438;
      --gold-pale: #f5ecd9;
      --navy: #1a2842;
      --navy-light: #2d3e5e;

      /* Fundos */
      --bg-page: #faf8f3;        /* off-white principal */
      --bg-card: #ffffff;         /* cards brancos */
      --bg-soft: #f0ede4;         /* secao secundaria */
      --line: #d8d3c4;
      --line-soft: #e8e3d4;

      /* Texto */
      --text-primary: #1a2842;
      --text-secondary: #6b6e76;
      --text-muted: #9a9690;

      /* Tier accents - mais sobrios pra combinar com a identidade */
      --tier1: #b91c1c;
      --tier1-bg: #fef2f2;
      --tier1-border: #fca5a5;
      --tier2: var(--navy);
      --tier2-bg: #eef1f6;
      --tier2-border: #b8c1d4;
      --tier3: var(--text-secondary);
      --tier3-bg: #f0ede4;
      --tier3-border: var(--line);

      /* Apoio */
      --green: #5d8c5b;
      --orange: #c2724a;
      --link: #3b5a8a;
    }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'Montserrat', sans-serif;
      background: var(--bg-page);
      color: var(--text-primary);
      min-height: 100vh;
      font-size: 14px;
    }
    header {
      background: var(--navy);
      color: white;
      padding: 14px 24px;
      box-shadow: 0 2px 12px rgba(26, 40, 66, 0.15);
      position: sticky;
      top: 0;
      z-index: 100;
    }
    .header-inner {
      max-width: 1400px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }
    .header-left {
      display: flex;
      align-items: center;
      gap: 16px;
    }
    .logo-img {
      height: 70px;
      width: auto;
      display: block;
    }
    .header-text-block {
      border-left: 1px solid rgba(255,255,255,0.15);
      padding-left: 16px;
    }
    .header-title {
      font-family: 'Cormorant Garamond', serif;
      font-size: 22px;
      font-weight: 600;
      letter-spacing: 0.3px;
    }
    .header-subtitle {
      font-size: 10px;
      letter-spacing: 2px;
      color: var(--gold-light);
      text-transform: uppercase;
      margin-top: 4px;
    }
    .btn {
      background: var(--gold);
      color: white;
      border: none;
      padding: 10px 18px;
      border-radius: 4px;
      font-family: 'Montserrat', sans-serif;
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 1px;
      text-transform: uppercase;
      cursor: pointer;
      transition: all 0.2s;
    }
    .btn:hover { background: var(--gold-light); }
    .btn:disabled { opacity: 0.5; cursor: not-allowed; }
    .btn-ghost {
      background: transparent;
      border: 1px solid rgba(187, 144, 76, 0.5);
      color: var(--gold-light);
    }
    .btn-ghost:hover {
      background: rgba(187, 144, 76, 0.1);
      border-color: var(--gold);
      color: white;
    }
    .btn-group { display: flex; gap: 8px; }

    .status-bar {
      max-width: 1400px;
      margin: 28px auto 0;
      padding: 0 24px;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
      gap: 12px;
    }
    .status-card {
      background: var(--bg-card);
      border-radius: 4px;
      padding: 14px 18px;
      border-left: 3px solid var(--gold);
      box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .status-card.tier1 { border-left-color: var(--tier1); }
    .status-card.tier2 { border-left-color: var(--tier2); }
    .status-card.tier3 { border-left-color: var(--tier3); }
    .status-card .label {
      font-size: 9px;
      color: var(--text-secondary);
      letter-spacing: 1.5px;
      text-transform: uppercase;
      margin-bottom: 8px;
      font-weight: 600;
    }
    .status-card .value {
      font-family: 'Cormorant Garamond', serif;
      font-size: 28px;
      color: var(--navy);
      font-weight: 600;
      line-height: 1;
    }
    .status-card .value.small {
      font-size: 12px;
      font-family: 'Montserrat', sans-serif;
      font-weight: 500;
    }

    .global-filters {
      max-width: 1400px;
      margin: 22px auto 0;
      padding: 0 24px;
    }
    .filters {
      display: flex;
      gap: 12px;
      align-items: center;
      flex-wrap: wrap;
      padding: 12px 16px;
      background: var(--bg-card);
      border-radius: 4px;
      border: 1px solid var(--line-soft);
    }
    .filters select, .filters label {
      font-size: 12px;
      font-family: 'Montserrat', sans-serif;
    }
    .filters select {
      padding: 6px 10px;
      border: 1px solid var(--line);
      border-radius: 3px;
      background: white;
      color: var(--navy);
      cursor: pointer;
    }
    .filters label {
      color: var(--text-secondary);
      display: flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
    }

    .tier-section {
      max-width: 1400px;
      margin: 32px auto 0;
      padding: 0 24px;
    }
    .tier-header {
      display: flex;
      align-items: center;
      gap: 14px;
      margin-bottom: 16px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--line);
    }
    .tier-pill {
      padding: 4px 14px;
      border-radius: 12px;
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 1.5px;
      text-transform: uppercase;
    }
    .tier-pill.tier1 { background: var(--tier1-bg); color: var(--tier1); border: 1px solid var(--tier1-border); }
    .tier-pill.tier2 { background: var(--tier2-bg); color: var(--tier2); border: 1px solid var(--tier2-border); }
    .tier-pill.tier3 { background: var(--tier3-bg); color: var(--tier3); border: 1px solid var(--tier3-border); }
    .tier-title {
      font-family: 'Cormorant Garamond', serif;
      font-size: 24px;
      font-weight: 600;
      color: var(--navy);
    }
    .tier-desc {
      font-size: 12px;
      color: var(--text-secondary);
      margin-left: auto;
      font-style: italic;
    }

    .phase-divider {
      display: flex;
      align-items: center;
      gap: 12px;
      margin: 22px 0 12px;
      font-size: 10px;
      letter-spacing: 1.8px;
      text-transform: uppercase;
      font-weight: 700;
      color: var(--text-secondary);
    }
    .phase-divider::before {
      content: '';
      width: 24px;
      height: 1px;
      background: var(--line);
    }
    .phase-divider::after {
      content: '';
      flex: 1;
      height: 1px;
      background: var(--line);
    }
    .phase-divider.antes { color: var(--green); }
    .phase-divider.apos { color: var(--orange); }

    .cards-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
      gap: 14px;
      margin-bottom: 8px;
    }

    .card {
      background: var(--bg-card);
      border-radius: 4px;
      padding: 18px 20px;
      border: 1px solid var(--line-soft);
      display: flex;
      flex-direction: column;
      gap: 10px;
      transition: all 0.2s;
      box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .card:hover {
      box-shadow: 0 8px 24px rgba(26, 40, 66, 0.08);
      border-color: var(--line);
      transform: translateY(-1px);
    }
    .card.tier1 { border-top: 3px solid var(--tier1); }
    .card.tier2 { border-top: 3px solid var(--tier2); }
    .card.tier3 { border-top: 3px solid var(--tier3); }

    .card-flag-row {
      display: flex;
      gap: 6px;
      align-items: center;
      flex-wrap: wrap;
    }
    .flag-badge {
      font-size: 9px;
      padding: 4px 9px;
      border-radius: 3px;
      font-weight: 700;
      letter-spacing: 1px;
      text-transform: uppercase;
    }
    .flag-badge.QUENTE { background: var(--tier1); color: white; }
    .flag-badge.TAFFASE { background: #c2410c; color: white; }
    .flag-badge.RECURSO { background: #b45309; color: white; }
    .flag-badge.VOLUME { background: var(--navy); color: white; }
    .flag-badge.JURISPRUDENCIA { background: #6d28d9; color: white; }
    .flag-badge.VIRAL { background: #be185d; color: white; }
    .flag-badge.CONCORRENCIA { background: #475569; color: white; }
    .relevancia {
      margin-left: auto;
      background: var(--gold-pale);
      color: var(--gold-dark);
      font-size: 10px;
      font-weight: 700;
      padding: 4px 9px;
      border-radius: 3px;
      letter-spacing: 0.5px;
    }
    .relevancia.alta { background: #fef3c7; color: #b45309; }
    .relevancia.maxima { background: var(--gold); color: white; }

    .card-title {
      font-family: 'Cormorant Garamond', serif;
      font-size: 19px;
      font-weight: 600;
      color: var(--navy);
      line-height: 1.3;
    }
    .card-subtitle {
      font-size: 12px;
      color: var(--text-secondary);
      line-height: 1.4;
      margin-top: -4px;
    }

    .card-concurso-info {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      padding: 12px 14px;
      background: linear-gradient(135deg, var(--gold-pale) 0%, var(--bg-page) 100%);
      border-radius: 4px;
      border-left: 2px solid var(--gold);
    }
    .info-block .info-label {
      font-size: 9px;
      color: var(--text-secondary);
      letter-spacing: 1.5px;
      text-transform: uppercase;
      margin-bottom: 3px;
      font-weight: 600;
    }
    .info-block .info-value {
      font-size: 15px;
      color: var(--navy);
      font-weight: 600;
      font-family: 'Cormorant Garamond', serif;
      letter-spacing: 0.3px;
    }
    .info-block .info-value.muted {
      color: var(--text-muted);
      font-style: italic;
      font-weight: 400;
    }

    .card-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
    }
    .badge {
      font-size: 10px;
      padding: 3px 9px;
      border-radius: 3px;
      background: var(--bg-soft);
      color: var(--text-secondary);
      font-weight: 500;
    }
    .badge.estado { background: #e0e7ff; color: #3730a3; }
    .badge.banca { background: #ecfdf5; color: #065f46; }
    .badge.fase { background: #fef3c7; color: #92400e; }
    .badge.data { background: var(--gold-pale); color: var(--gold-dark); }

    .card-desc {
      font-size: 13px;
      line-height: 1.55;
      color: var(--text-primary);
    }

    .extras {
      font-size: 11.5px;
      background: var(--bg-soft);
      padding: 10px 12px;
      border-radius: 4px;
      color: var(--text-secondary);
      line-height: 1.7;
    }
    .extras strong { color: var(--navy); font-weight: 600; }
    .extras .citacao {
      font-style: italic;
      color: var(--navy);
      border-left: 2px solid var(--gold);
      padding-left: 10px;
      margin-top: 6px;
      display: block;
      font-size: 12px;
    }

    .card-actions {
      display: flex;
      gap: 8px;
      margin-top: auto;
      padding-top: 10px;
      border-top: 1px solid var(--line-soft);
      align-items: center;
    }
    .card-action {
      background: transparent;
      border: 1px solid var(--line);
      color: var(--text-secondary);
      font-family: 'Montserrat', sans-serif;
      font-size: 10px;
      padding: 5px 11px;
      border-radius: 3px;
      cursor: pointer;
      transition: all 0.15s;
      letter-spacing: 0.5px;
      text-transform: uppercase;
      font-weight: 600;
    }
    .card-action:hover {
      border-color: var(--gold);
      color: var(--gold-dark);
      background: var(--gold-pale);
    }
    .card-link {
      color: var(--link);
      text-decoration: none;
      font-size: 11px;
      font-weight: 600;
      margin-left: auto;
    }
    .card-link:hover { text-decoration: underline; }

    .empty {
      text-align: center;
      padding: 36px 20px;
      color: var(--text-secondary);
      background: var(--bg-card);
      border-radius: 4px;
      border: 1px dashed var(--line);
    }
    .empty p {
      font-size: 13px;
      max-width: 480px;
      margin: 0 auto;
      line-height: 1.5;
    }

    .toast {
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: var(--navy);
      color: white;
      padding: 14px 22px;
      border-radius: 4px;
      box-shadow: 0 6px 24px rgba(0,0,0,0.25);
      font-size: 13px;
      z-index: 200;
      max-width: 420px;
    }
    .loading {
      text-align: center;
      padding: 40px 20px;
      color: var(--text-secondary);
    }
    .spinner {
      width: 32px;
      height: 32px;
      border: 3px solid var(--line);
      border-top-color: var(--gold);
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
      margin: 0 auto 14px;
    }
    @keyframes spin { to { transform: rotate(360deg); } }

    footer {
      max-width: 1400px;
      margin: 60px auto 30px;
      padding: 20px 24px;
      border-top: 1px solid var(--line);
      text-align: center;
      font-size: 11px;
      color: var(--text-muted);
      letter-spacing: 1px;
    }

    @media (max-width: 700px) {
      .logo-img { height: 50px; }
      .header-title { font-size: 17px; }
      .header-subtitle { display: none; }
      .header-text-block { padding-left: 12px; }
      .cards-grid { grid-template-columns: 1fr; }
      .btn { font-size: 10px; padding: 8px 12px; letter-spacing: 0.5px; }
      .card-concurso-info { grid-template-columns: 1fr; }
      .tier-desc { display: none; }
    }
  </style>
</head>
<body>
  <header>
    <div class="header-inner">
      <div class="header-left">
        <img class="logo-img" src="/logo.png" alt="Silva Pinto Advocacia">
        <div class="header-text-block">
          <div class="header-title">Painel de Oportunidades</div>
          <div class="header-subtitle">Captacao | Planejamento | Inteligencia</div>
        </div>
      </div>
      <div class="btn-group">
        <button class="btn btn-ghost" onclick="rodarTier(1)" id="btn-tier1">Coletar Tier 1</button>
        <button class="btn" onclick="rodarCompleto()" id="btn-completo">Coletar Tudo</button>
      </div>
    </div>
  </header>

  <div class="status-bar">
    <div class="status-card tier1">
      <div class="label">Tier 1 &mdash; Quente</div>
      <div class="value" id="stat-tier1">-</div>
    </div>
    <div class="status-card tier2">
      <div class="label">Tier 2 &mdash; Planejamento</div>
      <div class="value" id="stat-tier2">-</div>
    </div>
    <div class="status-card tier3">
      <div class="label">Tier 3 &mdash; Mercado</div>
      <div class="value" id="stat-tier3">-</div>
    </div>
    <div class="status-card">
      <div class="label">Total nao lidos</div>
      <div class="value" id="stat-nao-lidos">-</div>
    </div>
    <div class="status-card">
      <div class="label">Ultima coleta</div>
      <div class="value small" id="stat-ultima">-</div>
    </div>
  </div>

  <div class="global-filters">
    <div class="filters">
      <label><input type="checkbox" id="filtro-lidos"> mostrar lidos</label>
      <select id="filtro-estado">
        <option value="">Todos os estados</option>
        <option value="Brasil">Brasil (nacional)</option>
        <option value="MG">MG</option>
        <option value="ES">ES</option>
        <option value="RJ">RJ</option>
        <option value="SP">SP</option>
        <option value="DF">DF</option>
        <option value="BA">BA</option>
        <option value="PE">PE</option>
        <option value="RS">RS</option>
        <option value="PR">PR</option>
      </select>
      <button class="card-action" onclick="limparExemplos()" style="margin-left:auto">Limpar exemplos</button>
    </div>
  </div>

  <div class="tier-section" id="tier-1">
    <div class="tier-header">
      <span class="tier-pill tier1">Tier 1</span>
      <div class="tier-title">Captacao Imediata</div>
      <div class="tier-desc">Eliminacoes ativas | TAF | Recursos &mdash; acionar em ate 6h</div>
    </div>
    <div id="container-tier-1"><div class="loading"><div class="spinner"></div>Carregando...</div></div>
  </div>

  <div class="tier-section" id="tier-2">
    <div class="tier-header">
      <span class="tier-pill tier2">Tier 2</span>
      <div class="tier-title">Planejamento</div>
      <div class="tier-desc">Novos concursos | Jurisprudencia &mdash; estrategia de medio prazo</div>
    </div>
    <div id="container-tier-2"></div>
  </div>

  <div class="tier-section" id="tier-3" style="margin-bottom: 60px;">
    <div class="tier-header">
      <span class="tier-pill tier3">Tier 3</span>
      <div class="tier-title">Inteligencia de Mercado</div>
      <div class="tier-desc">Sentimento | Concorrencia &mdash; ideias para conteudo</div>
    </div>
    <div id="container-tier-3"></div>
  </div>

  <footer>
    Silva Pinto Advocacia &middot; OAB/RJ n&ordm; 189.781 &middot; Sistema Interno
  </footer>

  <script>
    let mostrarLidos = false;
    let filtroEstado = "";

    document.getElementById('filtro-lidos').addEventListener('change', e => {
      mostrarLidos = e.target.checked;
      carregarTudo();
    });
    document.getElementById('filtro-estado').addEventListener('change', e => {
      filtroEstado = e.target.value;
      carregarTudo();
    });

    function toast(msg, ms) {
      ms = ms || 4000;
      const el = document.createElement('div');
      el.className = 'toast';
      el.textContent = msg;
      document.body.appendChild(el);
      setTimeout(() => el.remove(), ms);
    }

    function fmtData(iso) {
      if (!iso) return '-';
      try {
        const d = new Date(iso);
        return d.toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
      } catch (e) { return iso.substring(0, 16); }
    }

    function escapeHtml(str) {
      if (!str) return '';
      return String(str).replace(/[&<>"']/g, c => ({
        '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
      }[c]));
    }

    async function carregarStatus() {
      try {
        const r = await fetch('/api/status');
        const data = await r.json();
        document.getElementById('stat-nao-lidos').textContent = data.nao_lidos;
        if (data.tier_counts) {
          document.getElementById('stat-tier1').textContent = data.tier_counts.tier1 || 0;
          document.getElementById('stat-tier2').textContent = data.tier_counts.tier2 || 0;
          document.getElementById('stat-tier3').textContent = data.tier_counts.tier3 || 0;
        }
        if (data.ultima_execucao) {
          const ue = data.ultima_execucao;
          let txt = fmtData(ue.data_execucao) + ' | ' + ue.itens_novos + ' novos';
          if (ue.tipo_run) txt += ' (' + ue.tipo_run + ')';
          if (!ue.sucesso) txt += ' [com erros]';
          document.getElementById('stat-ultima').textContent = txt;
        } else {
          document.getElementById('stat-ultima').textContent = 'Aguardando coleta';
        }
      } catch (e) { console.error(e); }
    }

    async function carregarTier(tier) {
      const container = document.getElementById('container-tier-' + tier);
      const params = new URLSearchParams();
      params.set('tier', tier);
      if (mostrarLidos) params.set('incluir_lidos', '1');
      if (filtroEstado) params.set('estado', filtroEstado);

      try {
        const r = await fetch('/api/oportunidades?' + params);
        const data = await r.json();
        renderizarTier(container, data.itens, tier);
      } catch (e) {
        container.innerHTML = '<div class="empty"><p>Erro ao carregar.</p></div>';
      }
    }

    function renderizarTier(container, itens, tier) {
      if (!itens.length) {
        let msg = 'Nenhuma oportunidade ' + (mostrarLidos ? '' : 'nao lida ') + 'no momento. ';
        if (tier === 1) msg += 'Tier 1 e atualizado as 09:00 e 17:00.';
        else msg += 'Tier 2 e 3 sao atualizados ao meio-dia.';
        container.innerHTML = '<div class="empty"><p>' + msg + '</p></div>';
        return;
      }

      if (tier === 1 || tier === 2) {
        const apos = itens.filter(i => i.etapa_concurso === 'apos_prova');
        const antes = itens.filter(i => i.etapa_concurso === 'antes_prova');
        const semEtapa = itens.filter(i => !i.etapa_concurso);

        let html = '';
        if (apos.length) {
          html += '<div class="phase-divider apos">Apos primeira etapa &middot; ' + apos.length + '</div>';
          html += '<div class="cards-grid">' + apos.map(renderCard).join('') + '</div>';
        }
        if (antes.length) {
          html += '<div class="phase-divider antes">Antes da prova objetiva &middot; ' + antes.length + '</div>';
          html += '<div class="cards-grid">' + antes.map(renderCard).join('') + '</div>';
        }
        if (semEtapa.length) {
          if (apos.length || antes.length) html += '<div class="phase-divider">Outros &middot; ' + semEtapa.length + '</div>';
          html += '<div class="cards-grid">' + semEtapa.map(renderCard).join('') + '</div>';
        }
        container.innerHTML = html;
      } else {
        container.innerHTML = '<div class="cards-grid">' + itens.map(renderCard).join('') + '</div>';
      }
    }

    function renderCard(item) {
      let relClass = '';
      if (item.relevancia >= 9) relClass = 'maxima';
      else if (item.relevancia >= 7) relClass = 'alta';

      const flagSafe = (item.flag || '').replace(/[^A-Z]/g, '');
      const flagPretty = (item.flag || '').replace('TAF/FASE', 'TAF').replace('CONCORRENCIA', 'CONCORR.');

      const isConcurso = (item.tier === 1 || item.tier === 2) && (item.vagas || item.salario || item.concurso);
      let concursoBlock = '';
      if (isConcurso && (item.vagas || item.salario)) {
        const vagasHtml = item.vagas
          ? '<div class="info-value">' + escapeHtml(item.vagas) + '</div>'
          : '<div class="info-value muted">nao informado</div>';
        const salarioHtml = item.salario
          ? '<div class="info-value">' + escapeHtml(item.salario) + '</div>'
          : '<div class="info-value muted">nao informado</div>';
        concursoBlock =
          '<div class="card-concurso-info">' +
            '<div class="info-block"><div class="info-label">Vagas</div>' + vagasHtml + '</div>' +
            '<div class="info-block"><div class="info-label">Salario</div>' + salarioHtml + '</div>' +
          '</div>';
      }

      let titleArea;
      if (item.concurso) {
        const cargoStr = item.cargo ? ' &middot; ' + escapeHtml(item.cargo) : '';
        titleArea = '<div class="card-title">' + escapeHtml(item.concurso) + cargoStr + '</div>';
        if (item.titulo && item.titulo !== item.concurso) {
          titleArea += '<div class="card-subtitle">' + escapeHtml(item.titulo) + '</div>';
        }
      } else {
        titleArea = '<div class="card-title">' + escapeHtml(item.titulo) + '</div>';
      }

      const badges = [];
      if (item.estado) badges.push('<span class="badge estado">' + escapeHtml(item.estado) + '</span>');
      if (item.banca) badges.push('<span class="badge banca">' + escapeHtml(item.banca) + '</span>');
      if (item.fase_atual) badges.push('<span class="badge fase">' + escapeHtml(item.fase_atual) + '</span>');
      if (item.prazo_inscricao) badges.push('<span class="badge fase">Inscr.: ' + escapeHtml(item.prazo_inscricao) + '</span>');
      if (item.data_prova) badges.push('<span class="badge">Prova: ' + escapeHtml(item.data_prova) + '</span>');
      if (item.data_publicacao) badges.push('<span class="badge data">' + escapeHtml(item.data_publicacao) + '</span>');

      let extrasBlock = '';
      if (item.extras && Object.keys(item.extras).length) {
        const extrasParts = [];
        for (const [k, v] of Object.entries(item.extras)) {
          if (!v) continue;
          if (k === 'citacao_candidato') {
            extrasParts.push('<div class="citacao">"' + escapeHtml(v) + '"</div>');
          } else {
            const labelMap = {
              'candidatos_estimados': 'Eliminados (est.)',
              'fase_eliminacao': 'Fase',
              'tipo_irregularidade': 'Tipo',
              'questao_numero': 'Questao',
              'afetados_estimados': 'Afetados',
              'tribunal': 'Tribunal',
              'tema': 'Tema',
              'numero_processo': 'Processo',
              'tese': 'Tese',
              'concurso_mencionado': 'Concurso',
              'padrao_emocional': 'Padrao',
              'escritorio_concorrente': 'Concorrente',
              'concurso_tema': 'Tema',
              'gap_identificado': 'Gap',
            };
            extrasParts.push('<strong>' + (labelMap[k] || k) + ':</strong> ' + escapeHtml(v));
          }
        }
        if (extrasParts.length) {
          extrasBlock = '<div class="extras">' + extrasParts.join(' &middot; ') + '</div>';
        }
      }

      const linkHtml = item.link ?
        '<a class="card-link" href="' + escapeHtml(item.link) + '" target="_blank" rel="noopener">Ver fonte &rarr;</a>' : '';

      return '<div class="card tier' + item.tier + '" data-id="' + item.id + '">' +
        '<div class="card-flag-row">' +
          '<span class="flag-badge ' + flagSafe + '">' + escapeHtml(flagPretty) + '</span>' +
          '<span class="relevancia ' + relClass + '">' + item.relevancia + '/10</span>' +
        '</div>' +
        titleArea +
        concursoBlock +
        (badges.length ? '<div class="card-meta">' + badges.join('') + '</div>' : '') +
        '<div class="card-desc">' + escapeHtml(item.descricao || '') + '</div>' +
        extrasBlock +
        '<div class="card-actions">' +
          '<button class="card-action" onclick="marcarLido(' + item.id + ')">Lido</button>' +
          '<button class="card-action" onclick="arquivar(' + item.id + ')">Arquivar</button>' +
          linkHtml +
        '</div>' +
      '</div>';
    }

    async function marcarLido(id) {
      try {
        await fetch('/api/oportunidades/' + id + '/marcar_lido', { method: 'POST' });
        const card = document.querySelector('.card[data-id="' + id + '"]');
        if (card) card.remove();
        carregarStatus();
      } catch (e) { toast('Erro ao marcar'); }
    }

    async function arquivar(id) {
      if (!confirm('Arquivar este item?')) return;
      try {
        await fetch('/api/oportunidades/' + id + '/arquivar', { method: 'POST' });
        const card = document.querySelector('.card[data-id="' + id + '"]');
        if (card) card.remove();
        carregarStatus();
      } catch (e) { toast('Erro ao arquivar'); }
    }

    async function limparExemplos() {
      if (!confirm('Apagar todos os itens [EXEMPLO] do banco?')) return;
      try {
        const r = await fetch('/api/limpar_exemplos', { method: 'POST' });
        const data = await r.json();
        toast(data.removidos + ' exemplos removidos');
        carregarStatus();
        carregarTudo();
      } catch (e) { toast('Erro'); }
    }

    async function rodarTier(tier) {
      const tipo = tier === 1 ? 'tier1' : 'tier23';
      const btn = document.getElementById('btn-tier' + tier);
      if (!confirm('Disparar coleta de Tier ' + tier + ' agora? Demora ~1-2 minutos.')) return;
      btn.disabled = true;
      btn.textContent = 'Coletando...';
      try {
        const r = await fetch('/cron/manual?tipo=' + tipo, { method: 'POST' });
        const data = await r.json();
        if (data.erro) { toast('Erro: ' + data.erro); btn.disabled = false; btn.textContent = 'Coletar Tier ' + tier; return; }
        toast(data.mensagem, 8000);
        startPolling(btn, 'Coletar Tier ' + tier);
      } catch (e) {
        toast('Erro');
        btn.disabled = false; btn.textContent = 'Coletar Tier ' + tier;
      }
    }

    async function rodarCompleto() {
      const btn = document.getElementById('btn-completo');
      if (!confirm('Disparar coleta COMPLETA (7 categorias)? Demora 3-6 minutos.')) return;
      btn.disabled = true;
      btn.textContent = 'Coletando...';
      try {
        const r = await fetch('/cron/manual?tipo=completo', { method: 'POST' });
        const data = await r.json();
        if (data.erro) { toast('Erro: ' + data.erro); btn.disabled = false; btn.textContent = 'Coletar Tudo'; return; }
        toast(data.mensagem, 10000);
        startPolling(btn, 'Coletar Tudo');
      } catch (e) {
        toast('Erro');
        btn.disabled = false; btn.textContent = 'Coletar Tudo';
      }
    }

    function startPolling(btn, txtFinal) {
      let polls = 0;
      const interval = setInterval(async () => {
        polls++;
        await carregarStatus();
        await carregarTudo();
        if (polls >= 30) {
          clearInterval(interval);
          btn.disabled = false;
          btn.textContent = txtFinal;
        }
      }, 12000);
    }

    function carregarTudo() {
      carregarTier(1);
      carregarTier(2);
      carregarTier(3);
    }

    carregarStatus();
    carregarTudo();

    setInterval(() => {
      carregarStatus();
      carregarTudo();
    }, 5 * 60 * 1000);
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))
    app.run(host="0.0.0.0", port=port, debug=False)
