"""
Silva Pinto Advocacia - Painel de Oportunidades v4
Single-file MVP com 7 categorias em 3 tiers.

Tier 1 (vermelho - captacao imediata): rodam 2x/dia (09:00 e 17:00 BRT)
  Cat 1 - Eliminacoes ativas
  Cat 2 - TAF e fases pos-prova
  Cat 3 - Questoes passiveis de recurso

Tier 2 (azul - planejamento): rodam 1x/dia (12:00 BRT)
  Cat 4 - Radar de volume (concursos novos)
  Cat 5 - Jurisprudencia estrategica

Tier 3 (cinza - inteligencia de mercado): rodam 1x/dia (12:00 BRT)
  Cat 6 - Sentimento do candidato
  Cat 7 - Movimentos da concorrencia

Modelo: Sonnet 4.5 (filtragem com mais nuance).
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
APP_VERSION = "v4-2026-05-04-tiers-completos"

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

app = Flask(__name__)


# Categorias com config
CATEGORIAS = {
    "elim_ativas": {
        "tier": 1,
        "label": "Eliminacoes ativas",
        "flag": "QUENTE",
        "queries": [
            "gabarito definitivo concurso publico {mes_ano}",
            "resultado final concurso publico eliminados {mes_ano}",
            "nota de corte concurso aprovados lista {mes_ano}",
            "PMERJ PCSC CBMDF PRF PF resultado 2026",
            "FGV Cebraspe Vunesp IDECAN gabarito polemica 2026",
        ],
        "descricao": (
            "Detectar o momento exato em que candidatos sao ELIMINADOS de concursos publicos. "
            "Foco em: gabaritos definitivos publicados HOJE/ESTA SEMANA, listas de resultados "
            "com candidatos eliminados, notas de corte recem-divulgadas. "
            "Esta e a JANELA DE MAIOR INTENCAO DE CONTRATACAO de advogado - candidatos com raiva, "
            "com medo, buscando solucao em tempo real. NAO incluir simples publicacoes de edital "
            "(isso e Cat 4). Foco em ELIMINACAO RECENTE."
        ),
        "campos_extras_obrigatorios": ["concurso", "banca", "fase_eliminacao", "candidatos_estimados"],
    },
    "taf_fases": {
        "tier": 1,
        "label": "TAF e fases pos-prova",
        "flag": "TAF/FASE",
        "queries": [
            "TAF concurso eliminados resultado {mes_ano}",
            "TAF concurso irregularidade reclamacao",
            "psicotecnico concurso inapto recurso 2026",
            "investigacao social eliminado concurso 2026",
            "exame medico inapto concurso policial 2026",
            "heteroidentificacao eliminado recurso concurso",
            "convocacao TAF concurso PMERJ PRF PM PC CBMDF 2026",
        ],
        "descricao": (
            "Detectar candidatos eliminados em FASES POS-PROVA OBJETIVA: TAF (teste de aptidao "
            "fisica), psicotecnico, investigacao social, exame medico, heteroidentificacao. "
            "Estas fases tem ALTA TAXA DE IRREGULARIDADE JURIDICA e os candidatos eliminados "
            "raramente sabem que podem contestar - alta conversao quando alcancados. "
            "Tambem incluir: convocacoes para essas fases (oportunidade de prepara-los antes)."
        ),
        "campos_extras_obrigatorios": ["concurso", "fase_eliminacao", "tipo_irregularidade"],
    },
    "recurso_anulacao": {
        "tier": 1,
        "label": "Questoes passiveis de recurso",
        "flag": "RECURSO",
        "queries": [
            "questao anulada banca concurso {mes_ano}",
            "gabarito definitivo alterado concurso {mes_ano}",
            "recursos deferidos banca concurso 2026",
            "questao passivel anulacao concurso professores 2026",
            "Estrategia Gran QConcursos questao polemica concurso 2026",
            "live correcao gabarito concurso 2026",
            "erros gabarito FGV Cebraspe Vunesp IDECAN 2026",
        ],
        "descricao": (
            "Detectar QUESTOES POLEMICAS de concursos recentes - candidatas a anulacao. "
            "Um unico erro sistemico afeta centenas de candidatos = oportunidade de acoes "
            "de massa. Foco em: questoes ja anuladas pela banca (= confirmacao de erro), "
            "questoes apontadas como polemicas por professores/cursinhos, recursos deferidos "
            "publicamente, gabaritos alterados. "
            "Detectar no D+0 (saida do gabarito) e essencial."
        ),
        "campos_extras_obrigatorios": ["concurso", "banca", "questao_numero", "afetados_estimados"],
    },
    "radar_volume": {
        "tier": 2,
        "label": "Radar de volume - novos concursos",
        "flag": "VOLUME",
        "queries": [
            "concurso publico inscritos {mes_ano} vagas",
            "edital concurso policial militar estado 2026",
            "concurso publico FGV Cebraspe Vunesp edital aberto",
            "novo edital PM PC guarda municipal 2026",
            "concurso federal vagas inscricoes abertas 2026",
            "pciconcursos concursos abertos {mes_ano}",
            "edital concurso publico seguranca publica 2026",
        ],
        "descricao": (
            "Identificar NOVOS CONCURSOS abertos (com inscricoes ainda vigentes ou recem-encerradas, "
            "AINDA SEM PROVA OBJETIVA REALIZADA). Priorizar: alto volume de inscritos (50k+ "
            "= prioridade A), bancas FGV/Cebraspe/Vunesp (tese conhecida), seguranca publica "
            "(forte para o escritorio). Para cada concurso INFORMAR EXPLICITAMENTE: "
            "numero de vagas, salario inicial, banca, prazo de inscricao, data prevista da prova. "
            "Estes dados sao OBRIGATORIOS no card."
        ),
        "campos_extras_obrigatorios": ["concurso", "cargo", "vagas", "salario", "banca", "prazo_inscricao", "data_prova"],
    },
    "jurisprudencia": {
        "tier": 2,
        "label": "Jurisprudencia estrategica",
        "flag": "JURISPRUDENCIA",
        "queries": [
            "STJ decisao concurso publico candidato 2026",
            "STF sumula concurso publico eliminacao 2026",
            "TJ liminar concurso publico candidato deferida 2026",
            "mandado de seguranca concurso STJ 2026",
            "TAF ilegal decisao judicial 2026",
            "investigacao social STJ inconstitucional 2026",
            "candidato aprovado nomeacao direito STF 2026",
            "heteroidentificacao STF decisao 2026",
        ],
        "descricao": (
            "Decisoes de TRIBUNAIS SUPERIORES (STJ, STF) e TJs FAVORAVEIS aos candidatos "
            "em concursos publicos. APENAS DECISOES DOS ULTIMOS 12 MESES. Foco em: "
            "decisoes que reforcam teses do escritorio, novas janelas de contestacao "
            "ainda pouco exploradas. EXTRAIR: tribunal, tema da decisao, numero do processo "
            "quando disponivel. Util para conteudo de autoridade e atualizacao de argumentos."
        ),
        "campos_extras_obrigatorios": ["tribunal", "tema", "numero_processo", "tese"],
    },
    "sentimento": {
        "tier": 3,
        "label": "Sentimento do candidato",
        "flag": "VIRAL",
        "queries": [
            "fui eliminado concurso o que fazer 2026",
            "eliminado TAF injustamente concurso 2026",
            "gabarito errado concurso reclamacao candidatos {mes_ano}",
            "concurso eliminados investigacao social absurdo 2026",
            "psicotecnico reprovado sem motivo concurso 2026",
            "site:reddit.com eliminado concurso 2026",
            "telegram grupo eliminados recurso concurso",
        ],
        "descricao": (
            "Onde candidatos DESABAFAM antes de buscar advogado: foruns (Reddit, "
            "QConcursos), grupos de Telegram, Youtube. Detectar PADROES DE REVOLTA "
            "e URGENCIA. Util para: hooks de Reels (citacao real do candidato), "
            "temas de carrossel, ideias de conteudo viral, identificar objecoes novas. "
            "EXTRAIR sempre que possivel a CITACAO LITERAL do candidato (entre aspas) "
            "para usar como hook. APENAS conteudo dos ultimos 12 meses."
        ),
        "campos_extras_obrigatorios": ["citacao_candidato", "concurso_mencionado", "padrao_emocional"],
    },
    "concorrencia": {
        "tier": 3,
        "label": "Movimentos da concorrencia",
        "flag": "CONCORRENCIA",
        "queries": [
            "safeelimaadv concurso liminar 2026",
            "queromeuconcurso concurso liminar 2026",
            "marcuspeterson concursos recurso 2026",
            "advogado concurso publico liminar viral 2026",
            "escritorio concurso publico liminar cidade 2026",
            "advocacia concurso publico viral instagram 2026",
        ],
        "descricao": (
            "Monitorar 3 CONCORRENTES DIRETOS: Safe & Lima, Queromeuconcurso, "
            "Marcus Peterson. Detectar quando estao entrando em concursos novos, "
            "lancando conteudo viral ou explorando teses ainda nao exploradas. "
            "EXTRAIR: nome do escritorio, concurso/tema explorado, gap identificado "
            "(o que eles fazem que Silva Pinto ainda nao faz). APENAS atividades "
            "dos ultimos 12 meses."
        ),
        "campos_extras_obrigatorios": ["escritorio_concorrente", "concurso_tema", "gap_identificado"],
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
    """Substitui {mes_ano} pelas queries da categoria."""
    mes_ano = hoje.strftime("%B %Y").lower()
    mes_pt = {
        "january": "janeiro", "february": "fevereiro", "march": "marco",
        "april": "abril", "may": "maio", "june": "junho",
        "july": "julho", "august": "agosto", "september": "setembro",
        "october": "outubro", "november": "novembro", "december": "dezembro",
    }
    for en, pt in mes_pt.items():
        mes_ano = mes_ano.replace(en, pt)

    return [q.replace("{mes_ano}", mes_ano) for q in queries_template]


FONTES_PRIORITARIAS = """
PRIORIZE estas fontes na busca (alta confiabilidade):
- pciconcursos.com.br, qconcursos.com, estrategiaconcursos.com.br
- grancursosonline.com.br, novaconcursos.com.br
- jusbrasil.com.br, migalhas.com.br, conjur.com.br
- stj.jus.br, stf.jus.br (sites oficiais de tribunais)
- Sites oficiais de bancas (FGV, Cebraspe, Vunesp, IDECAN, IBADE)
- Sites oficiais dos orgaos (PMs, PCs, ministerios)

Para Tier 3 (sentimento/concorrencia): aceite reddit, instagram, youtube, tiktok, telegram.
"""


def coletar_categoria(api_key, cat_id, hoje):
    cat = CATEGORIAS[cat_id]
    queries = render_queries(cat["queries"], hoje)
    descricao = cat["descricao"]
    flag = cat["flag"]
    tier = cat["tier"]
    extras = cat.get("campos_extras_obrigatorios", [])

    todos_itens = []
    erro_msg = None

    extras_json_template = ""
    if extras:
        extras_json_template = ",\n      ".join(f'"{c}": "valor ou vazio"' for c in extras)
        extras_json_template = f",\n      {extras_json_template}"

    queries_str = "\n".join(f"  {i+1}. {q}" for i, q in enumerate(queries))

    # Etapa do concurso (so para concursos)
    etapa_block = ""
    if cat_id in ("elim_ativas", "taf_fases", "recurso_anulacao", "radar_volume"):
        etapa_block = """
- "etapa_concurso": OBRIGATORIO. Use APENAS UM destes valores:
    "antes_prova" = concurso ainda nao realizou prova objetiva (edital aberto, inscricoes, etc)
    "apos_prova"  = prova objetiva ja realizada (gabarito, recursos, TAF, fase posterior)
"""

    prompt = f"""Voce e um pesquisador juridico do escritorio Silva Pinto Advocacia, especializado em concursos publicos.

CATEGORIA: {cat['label']} (Tier {tier})

OBJETIVO: {descricao}

{FONTES_PRIORITARIAS}

RESTRICAO TEMPORAL: APENAS conteudo dos ULTIMOS 12 MESES. Descarte qualquer materia/decisao/post mais antigo.

Realize as buscas a seguir, uma por vez, usando a ferramenta de busca:
{queries_str}

Apos as buscas, retorne JSON estruturado com no MAXIMO 8 itens, escolhidos pelos mais relevantes/recentes.

FORMATO (JSON puro, sem markdown, sem texto antes/depois):
{{
  "itens": [
    {{
      "titulo": "Titulo objetivo e direto, com nome do concurso quando aplicavel",
      "descricao": "Resumo em 2-3 frases, com dados concretos quando disponiveis",
      "orgao": "Orgao/instituicao (ex: PCMG, STJ, TJ-SP) ou vazio",
      "estado": "UF (ex: MG, SP) ou Brasil se nacional",
      "concurso": "Nome curto do concurso (ex: PMERJ 2026, PRF 2026, Receita Federal 2026) ou vazio",
      "cargo": "Cargo do concurso (ex: Soldado, Investigador) ou vazio",
      "banca": "Banca examinadora (FGV, Cebraspe, etc) ou vazio",
      "vagas": "Numero de vagas (ex: 1800, 250+CR) ou vazio",
      "salario": "Salario inicial em R$ (ex: R$ 6.500,00) ou vazio",
      "prazo_inscricao": "Data limite de inscricao (ex: 30/06/2026) ou vazio",
      "data_prova": "Data prevista da prova objetiva ou vazio",
      "fase_atual": "Fase em que o concurso esta (ex: inscricoes abertas, gabarito definitivo, TAF) ou vazio",
      "link": "URL da fonte mais confiavel",
      "relevancia": 1-10 (impacto/urgencia para captacao de leads){etras_block}{etapa_block_inline}
    }}
  ]
}}

REGRAS IMPORTANTES:
- A categoria "{cat['label']}" e flag "{flag}" sao APLICADAS PELO SISTEMA - voce NAO precisa incluir.
- NAO duplique itens (mesmo concurso, mesmo tema = um item so).
- Se nada relevante, retorne {{"itens": []}}.
- Para CONCURSOS: tente sempre preencher vagas e salario - sao decisivos para o card.
- Retorne SO o JSON, sem nada antes/depois."""

    # Replace placeholders
    extras_block_for_extras = extras_json_template if extras else ""
    etapa_block_inline_for_etapa = etapa_block if etapa_block else ""
    prompt = prompt.replace("{etras_block}", extras_block_for_extras)
    prompt = prompt.replace("{etapa_block_inline}", etapa_block_inline_for_etapa)

    try:
        log.info("[%s tier%d] iniciando %d buscas", cat_id, tier, len(queries))
        client = anthropic.Anthropic(api_key=api_key, timeout=240.0, max_retries=2)
        msg = client.messages.create(
            model=MODEL_NAME,
            max_tokens=12000,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{"role": "user", "content": prompt}],
        )

        text_parts = []
        for block in msg.content:
            if hasattr(block, "text") and block.text:
                text_parts.append(block.text)
        raw = "".join(text_parts).strip()

        log.info("[%s] resposta: %d chars", cat_id, len(raw))

        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```\s*$", "", raw)

        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not json_match:
            return [], "JSON nao encontrado"

        try:
            data = json.loads(json_match.group(0))
        except json.JSONDecodeError as e:
            return [], f"JSON malformado: {e}"

        itens = data.get("itens", [])
        log.info("[%s] %d itens extraidos", cat_id, len(itens))

        for item in itens:
            if not isinstance(item, dict) or not item.get("titulo"):
                continue

            # Build extras dict (campos especificos da categoria)
            extras_dict = {}
            for campo in extras:
                v = item.get(campo)
                if v:
                    extras_dict[campo] = str(v)[:300]

            etapa = item.get("etapa_concurso", "").strip().lower()
            if etapa not in ("antes_prova", "apos_prova"):
                etapa = ""

            todos_itens.append({
                "categoria": cat_id,
                "tier": tier,
                "flag": flag,
                "titulo": str(item.get("titulo", "")).strip()[:300],
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
                "extras_json": json.dumps(extras_dict, ensure_ascii=False) if extras_dict else "",
                "link": str(item.get("link", "")).strip()[:500],
                "relevancia": int(item.get("relevancia", 5)) if str(item.get("relevancia", 5)).isdigit() else 5,
                "etapa_concurso": etapa,
            })

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
                     data_prova, fase_atual, extras_json, link, relevancia,
                     etapa_concurso, data_coleta, hash_unico)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (item["categoria"], item["tier"], item["flag"],
                     item["titulo"], item["descricao"], item["orgao"], item["estado"],
                     item["concurso"], item["cargo"], item["banca"], item["vagas"],
                     item["salario"], item["prazo_inscricao"], item["data_prova"],
                     item["fase_atual"], item["extras_json"], item["link"],
                     item["relevancia"], item["etapa_concurso"], agora, h)
                )
                novos += 1
            except sqlite3.IntegrityError:
                pass
    return novos


def executar_coleta(api_key, categorias_a_rodar, tipo_run="manual"):
    """Executa coleta para uma lista especifica de categorias."""
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
        # Parse extras_json
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
        # Contagens por tier
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
    """Endpoint chamado as 09:00 e 17:00 BRT - so categorias quentes."""
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
    """Endpoint chamado 1x/dia (12:00 BRT) - tiers 2 e 3 juntos."""
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
    """Disparo manual via UI - executa TODAS as categorias."""
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


def seed_demo_se_vazio():
    with db_conn() as conn:
        count = conn.execute("SELECT COUNT(*) AS c FROM oportunidades").fetchone()["c"]
        if count > 0:
            return
        log.info("Banco vazio - inserindo dados de exemplo")
        agora = datetime.now(timezone.utc).isoformat()
        demos = [
            # Tier 1
            {
                "categoria": "elim_ativas", "tier": 1, "flag": "QUENTE",
                "titulo": "[EXEMPLO] PCDF: gabarito definitivo elimina 1.200 candidatos",
                "descricao": "Banca FGV publicou gabarito definitivo do concurso PCDF 2026. Estima-se que 1.200 candidatos foram eliminados na prova objetiva. Janela curta para impugnacao judicial.",
                "orgao": "PCDF", "estado": "DF",
                "concurso": "PCDF 2026", "cargo": "Agente", "banca": "FGV",
                "vagas": "1800", "salario": "R$ 7.300,00",
                "prazo_inscricao": "", "data_prova": "Realizada em 15/04/2026",
                "fase_atual": "Gabarito definitivo publicado",
                "etapa_concurso": "apos_prova",
                "extras_json": json.dumps({"candidatos_estimados": "1200", "fase_eliminacao": "objetiva"}),
                "link": "https://example.com", "relevancia": 10,
            },
            {
                "categoria": "taf_fases", "tier": 1, "flag": "TAF/FASE",
                "titulo": "[EXEMPLO] PMERJ: TAF marcado para 20/05 com 3.500 convocados",
                "descricao": "Convocacao para TAF do concurso PMERJ 2026. Historicamente 30% dos convocados sao eliminados nesta fase. Oportunidade preventiva.",
                "orgao": "PMERJ", "estado": "RJ",
                "concurso": "PMERJ 2026", "cargo": "Soldado", "banca": "Cebraspe",
                "vagas": "3000", "salario": "R$ 4.800,00",
                "fase_atual": "Convocacao para TAF",
                "etapa_concurso": "apos_prova",
                "extras_json": json.dumps({"fase_eliminacao": "TAF", "tipo_irregularidade": "criterios subjetivos"}),
                "link": "https://example.com", "relevancia": 9,
            },
            {
                "categoria": "recurso_anulacao", "tier": 1, "flag": "RECURSO",
                "titulo": "[EXEMPLO] Concurso PRF 2026: questao 47 com gabarito polemico",
                "descricao": "Professores apontam erro grosseiro na questao 47 da prova de Direito Constitucional. Estima-se 8.000 candidatos prejudicados. Banca ainda nao se manifestou.",
                "orgao": "PRF", "estado": "Brasil",
                "concurso": "PRF 2026", "cargo": "Policial Rodoviario", "banca": "Cebraspe",
                "fase_atual": "Recursos contra gabarito preliminar",
                "etapa_concurso": "apos_prova",
                "extras_json": json.dumps({"questao_numero": "47", "afetados_estimados": "8000"}),
                "link": "https://example.com", "relevancia": 9,
            },
            # Tier 2
            {
                "categoria": "radar_volume", "tier": 2, "flag": "VOLUME",
                "titulo": "[EXEMPLO] Receita Federal abre concurso com 230 vagas",
                "descricao": "Edital publicado com 230 vagas para Auditor Fiscal. Salario inicial alto. Banca FGV. Inscricoes ate o final do mes.",
                "orgao": "Receita Federal", "estado": "Brasil",
                "concurso": "Receita Federal 2026", "cargo": "Auditor Fiscal", "banca": "FGV",
                "vagas": "230", "salario": "R$ 21.029,09",
                "prazo_inscricao": "30/06/2026", "data_prova": "15/09/2026",
                "fase_atual": "Inscricoes abertas",
                "etapa_concurso": "antes_prova",
                "extras_json": "",
                "link": "https://example.com", "relevancia": 10,
            },
            {
                "categoria": "jurisprudencia", "tier": 2, "flag": "JURISPRUDENCIA",
                "titulo": "[EXEMPLO] STJ: questao fora do edital deve ser anulada mesmo apos gabarito definitivo",
                "descricao": "STJ firmou entendimento de que questoes cobradas fora do conteudo programatico do edital devem ser anuladas. Tese reforca atuacao do escritorio.",
                "orgao": "STJ", "estado": "Brasil",
                "fase_atual": "",
                "etapa_concurso": "",
                "extras_json": json.dumps({"tribunal": "STJ", "tema": "questao fora do edital", "numero_processo": "REsp 1.234.567/SP"}),
                "link": "https://example.com", "relevancia": 9,
            },
            # Tier 3
            {
                "categoria": "sentimento", "tier": 3, "flag": "VIRAL",
                "titulo": "[EXEMPLO] Reddit: candidato relata eliminacao injusta em TAF",
                "descricao": "Post viralizou no r/concurseiros: 'Fui eliminado por 1 segundo na corrida e a banca se recusa a ouvir recurso'. 340 comentarios.",
                "orgao": "", "estado": "",
                "fase_atual": "",
                "etapa_concurso": "",
                "extras_json": json.dumps({"citacao_candidato": "Fui eliminado por 1 segundo na corrida", "padrao_emocional": "indignacao + impotencia"}),
                "link": "https://example.com", "relevancia": 7,
            },
            {
                "categoria": "concorrencia", "tier": 3, "flag": "CONCORRENCIA",
                "titulo": "[EXEMPLO] Safe & Lima entra em PMERJ 2026 com tese nova",
                "descricao": "Concorrente Safe & Lima publicou Reel sobre tese de inconstitucionalidade do criterio de altura no TAF. Tese ainda nao explorada por Silva Pinto.",
                "orgao": "", "estado": "",
                "fase_atual": "",
                "etapa_concurso": "",
                "extras_json": json.dumps({"escritorio_concorrente": "Safe & Lima", "concurso_tema": "PMERJ 2026 - TAF altura", "gap_identificado": "tese de inconstitucionalidade ainda nao usada"}),
                "link": "https://example.com", "relevancia": 8,
            },
        ]
        for d in demos:
            try:
                conn.execute(
                    """INSERT INTO oportunidades
                    (categoria, tier, flag, titulo, descricao, orgao, estado,
                     concurso, cargo, banca, vagas, salario, prazo_inscricao,
                     data_prova, fase_atual, extras_json, link, relevancia,
                     etapa_concurso, data_coleta, hash_unico)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (d["categoria"], d["tier"], d["flag"], d["titulo"], d["descricao"],
                     d.get("orgao", ""), d.get("estado", ""), d.get("concurso", ""),
                     d.get("cargo", ""), d.get("banca", ""), d.get("vagas", ""),
                     d.get("salario", ""), d.get("prazo_inscricao", ""),
                     d.get("data_prova", ""), d.get("fase_atual", ""),
                     d.get("extras_json", ""), d.get("link", ""), d["relevancia"],
                     d.get("etapa_concurso", ""), agora,
                     hash_for_dedup(d["titulo"], d.get("orgao", "")))
                )
            except sqlite3.IntegrityError:
                pass


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
      --gold: #BB904C;
      --gold-light: #D4AF7A;
      --gold-pale: #f5ecd9;
      --navy: #1a2842;
      --navy-light: #2d3e5e;
      --gray-bg: #f4f4f0;
      --gray-line: #d8d8d2;
      --text-primary: #1a2842;
      --text-secondary: #6b6e76;
      --tier1: #b91c1c;
      --tier1-bg: #fef2f2;
      --tier1-border: #fca5a5;
      --tier2: #1d4ed8;
      --tier2-bg: #eff6ff;
      --tier2-border: #93c5fd;
      --tier3: #6b6e76;
      --tier3-bg: #f4f4f0;
      --tier3-border: #d1d5db;
      --green: #059669;
      --orange: #d97706;
      --blue: #2563eb;
    }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'Montserrat', sans-serif;
      background: var(--gray-bg);
      color: var(--text-primary);
      min-height: 100vh;
    }
    header {
      background: var(--navy);
      color: white;
      padding: 16px 24px;
      box-shadow: 0 2px 12px rgba(0,0,0,0.2);
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
      gap: 14px;
    }
    .logo-mark {
      width: 44px;
      height: 44px;
      border: 1.5px solid var(--gold);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: 'Cormorant Garamond', serif;
      font-size: 22px;
      font-weight: 700;
      color: var(--gold);
      letter-spacing: 1px;
    }
    .header-title {
      font-family: 'Cormorant Garamond', serif;
      font-size: 22px;
      font-weight: 600;
    }
    .header-subtitle {
      font-size: 11px;
      letter-spacing: 1.5px;
      color: var(--gold-light);
      text-transform: uppercase;
      margin-top: 2px;
    }
    .btn {
      background: var(--gold);
      color: white;
      border: none;
      padding: 10px 16px;
      border-radius: 5px;
      font-family: 'Montserrat', sans-serif;
      font-size: 12px;
      font-weight: 600;
      letter-spacing: 0.5px;
      text-transform: uppercase;
      cursor: pointer;
      transition: all 0.15s;
    }
    .btn:hover { background: var(--gold-light); }
    .btn:disabled { opacity: 0.5; cursor: not-allowed; }
    .btn-ghost {
      background: transparent;
      border: 1px solid rgba(255,255,255,0.3);
      color: white;
    }
    .btn-ghost:hover { background: rgba(255,255,255,0.1); }
    .btn-group { display: flex; gap: 8px; }
    .btn-sm { font-size: 11px; padding: 8px 12px; }

    .status-bar {
      max-width: 1400px;
      margin: 24px auto 0;
      padding: 0 24px;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 12px;
    }
    .status-card {
      background: white;
      border-radius: 6px;
      padding: 14px 16px;
      border-left: 3px solid var(--gold);
    }
    .status-card.tier1 { border-left-color: var(--tier1); }
    .status-card.tier2 { border-left-color: var(--tier2); }
    .status-card.tier3 { border-left-color: var(--tier3); }
    .status-card .label {
      font-size: 10px;
      color: var(--text-secondary);
      letter-spacing: 1px;
      text-transform: uppercase;
      margin-bottom: 6px;
    }
    .status-card .value {
      font-family: 'Cormorant Garamond', serif;
      font-size: 26px;
      color: var(--navy);
      font-weight: 600;
    }
    .status-card .value.small {
      font-size: 13px;
      font-family: 'Montserrat', sans-serif;
    }

    .tier-section {
      max-width: 1400px;
      margin: 28px auto 0;
      padding: 0 24px;
    }
    .tier-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 14px;
      padding-bottom: 10px;
      border-bottom: 1px solid var(--gray-line);
    }
    .tier-pill {
      padding: 4px 12px;
      border-radius: 12px;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 1px;
      text-transform: uppercase;
    }
    .tier-pill.tier1 { background: var(--tier1-bg); color: var(--tier1); border: 1px solid var(--tier1-border); }
    .tier-pill.tier2 { background: var(--tier2-bg); color: var(--tier2); border: 1px solid var(--tier2-border); }
    .tier-pill.tier3 { background: var(--tier3-bg); color: var(--tier3); border: 1px solid var(--tier3-border); }
    .tier-title {
      font-family: 'Cormorant Garamond', serif;
      font-size: 22px;
      font-weight: 600;
      color: var(--navy);
    }
    .tier-desc {
      font-size: 12px;
      color: var(--text-secondary);
      margin-left: auto;
    }

    .filters {
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
      margin-bottom: 12px;
    }
    .filters select, .filters label {
      font-size: 12px;
    }
    .filters select {
      padding: 6px 10px;
      border: 1px solid var(--gray-line);
      border-radius: 4px;
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

    .phase-divider {
      display: flex;
      align-items: center;
      gap: 10px;
      margin: 18px 0 10px;
      font-size: 11px;
      letter-spacing: 1.5px;
      text-transform: uppercase;
      font-weight: 600;
      color: var(--text-secondary);
    }
    .phase-divider::before {
      content: '';
      flex: 1;
      height: 1px;
      background: var(--gray-line);
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
      background: white;
      border-radius: 6px;
      padding: 16px 18px;
      border: 1px solid var(--gray-line);
      display: flex;
      flex-direction: column;
      gap: 10px;
      transition: box-shadow 0.15s, transform 0.15s;
    }
    .card:hover {
      box-shadow: 0 8px 24px rgba(26, 40, 66, 0.08);
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
      margin-bottom: 2px;
    }
    .flag-badge {
      font-size: 10px;
      padding: 3px 8px;
      border-radius: 3px;
      font-weight: 700;
      letter-spacing: 0.5px;
    }
    .flag-badge.QUENTE { background: var(--tier1); color: white; }
    .flag-badge.TAFFASE { background: #c2410c; color: white; }
    .flag-badge.RECURSO { background: #b45309; color: white; }
    .flag-badge.VOLUME { background: var(--tier2); color: white; }
    .flag-badge.JURISPRUDENCIA { background: #7c3aed; color: white; }
    .flag-badge.VIRAL { background: #be185d; color: white; }
    .flag-badge.CONCORRENCIA { background: #475569; color: white; }
    .relevancia {
      margin-left: auto;
      background: var(--gold-pale);
      color: var(--gold);
      font-size: 11px;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 3px;
    }
    .relevancia.alta { background: #fef3c7; color: #b45309; }
    .relevancia.maxima { background: var(--gold); color: white; }

    .card-title {
      font-family: 'Cormorant Garamond', serif;
      font-size: 18px;
      font-weight: 600;
      color: var(--navy);
      line-height: 1.3;
    }

    .card-concurso-info {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      padding: 10px;
      background: linear-gradient(to right, var(--gold-pale), #fff);
      border-radius: 5px;
      border-left: 2px solid var(--gold);
    }
    .info-block .info-label {
      font-size: 9px;
      color: var(--text-secondary);
      letter-spacing: 1px;
      text-transform: uppercase;
      margin-bottom: 2px;
    }
    .info-block .info-value {
      font-size: 14px;
      color: var(--navy);
      font-weight: 600;
      font-family: 'Cormorant Garamond', serif;
    }

    .card-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
    }
    .badge {
      font-size: 10px;
      padding: 3px 8px;
      border-radius: 3px;
      background: var(--gray-bg);
      color: var(--text-secondary);
      font-weight: 500;
    }
    .badge.estado { background: #e0e7ff; color: #3730a3; }
    .badge.banca { background: #ecfdf5; color: #065f46; }
    .badge.fase { background: #fef3c7; color: #92400e; }

    .card-desc {
      font-size: 13px;
      line-height: 1.5;
      color: var(--text-primary);
    }

    .extras {
      font-size: 11px;
      background: var(--gray-bg);
      padding: 8px 10px;
      border-radius: 4px;
      color: var(--text-secondary);
      line-height: 1.7;
    }
    .extras strong { color: var(--navy); font-weight: 600; }
    .extras .citacao {
      font-style: italic;
      color: var(--navy);
      border-left: 2px solid var(--gold);
      padding-left: 8px;
      margin-top: 4px;
    }

    .card-actions {
      display: flex;
      gap: 8px;
      margin-top: auto;
      padding-top: 8px;
      border-top: 1px solid var(--gray-bg);
      align-items: center;
    }
    .card-action {
      background: transparent;
      border: 1px solid var(--gray-line);
      color: var(--text-secondary);
      font-family: 'Montserrat', sans-serif;
      font-size: 11px;
      padding: 5px 10px;
      border-radius: 4px;
      cursor: pointer;
      transition: all 0.15s;
    }
    .card-action:hover {
      border-color: var(--gold);
      color: var(--gold);
    }
    .card-link {
      color: var(--blue);
      text-decoration: none;
      font-size: 11px;
      font-weight: 500;
      margin-left: auto;
    }
    .card-link:hover { text-decoration: underline; }

    .empty {
      text-align: center;
      padding: 40px 20px;
      color: var(--text-secondary);
      background: white;
      border-radius: 8px;
      border: 1px dashed var(--gray-line);
    }
    .empty p {
      font-size: 13px;
      max-width: 480px;
      margin: 0 auto;
    }

    .toast {
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: var(--navy);
      color: white;
      padding: 14px 22px;
      border-radius: 6px;
      box-shadow: 0 6px 20px rgba(0,0,0,0.2);
      font-size: 13px;
      z-index: 200;
      max-width: 400px;
    }
    .loading {
      text-align: center;
      padding: 50px 20px;
      color: var(--text-secondary);
    }
    .spinner {
      width: 32px;
      height: 32px;
      border: 3px solid var(--gray-line);
      border-top-color: var(--gold);
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
      margin: 0 auto 14px;
    }
    @keyframes spin { to { transform: rotate(360deg); } }

    @media (max-width: 700px) {
      .header-title { font-size: 18px; }
      .header-subtitle { display: none; }
      .cards-grid { grid-template-columns: 1fr; }
      .btn { font-size: 11px; padding: 8px 12px; }
      .card-concurso-info { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <div class="header-inner">
      <div class="header-left">
        <div class="logo-mark">SP</div>
        <div>
          <div class="header-title">Painel de Oportunidades</div>
          <div class="header-subtitle">Captacao | Planejamento | Inteligencia de Mercado</div>
        </div>
      </div>
      <div class="btn-group">
        <button class="btn btn-ghost btn-sm" onclick="rodarTier(1)" id="btn-tier1">Coletar Tier 1</button>
        <button class="btn btn-ghost btn-sm" onclick="rodarCompleto()" id="btn-completo">Coletar tudo</button>
      </div>
    </div>
  </header>

  <div class="status-bar">
    <div class="status-card tier1">
      <div class="label">Tier 1 (quente)</div>
      <div class="value" id="stat-tier1">-</div>
    </div>
    <div class="status-card tier2">
      <div class="label">Tier 2 (planejamento)</div>
      <div class="value" id="stat-tier2">-</div>
    </div>
    <div class="status-card tier3">
      <div class="label">Tier 3 (mercado)</div>
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

  <div style="max-width: 1400px; margin: 20px auto 0; padding: 0 24px;">
    <div class="filters">
      <label><input type="checkbox" id="filtro-lidos"> mostrar lidos tambem</label>
      <select id="filtro-estado">
        <option value="">Todos os estados</option>
        <option value="Brasil">Brasil (nacional)</option>
        <option value="MG">MG</option>
        <option value="ES">ES</option>
        <option value="RJ">RJ</option>
        <option value="SP">SP</option>
        <option value="DF">DF</option>
      </select>
    </div>
  </div>

  <!-- Tier 1 -->
  <div class="tier-section" id="tier-1">
    <div class="tier-header">
      <span class="tier-pill tier1">Tier 1</span>
      <div class="tier-title">Captacao Imediata</div>
      <div class="tier-desc">Eliminacoes ativas | TAF | Recursos &mdash; acionar em ate 6h</div>
    </div>
    <div id="container-tier-1"><div class="loading"><div class="spinner"></div>Carregando...</div></div>
  </div>

  <!-- Tier 2 -->
  <div class="tier-section" id="tier-2">
    <div class="tier-header">
      <span class="tier-pill tier2">Tier 2</span>
      <div class="tier-title">Planejamento</div>
      <div class="tier-desc">Novos concursos | Jurisprudencia &mdash; estrategia de medio prazo</div>
    </div>
    <div id="container-tier-2"></div>
  </div>

  <!-- Tier 3 -->
  <div class="tier-section" id="tier-3" style="margin-bottom: 60px;">
    <div class="tier-header">
      <span class="tier-pill tier3">Tier 3</span>
      <div class="tier-title">Inteligencia de Mercado</div>
      <div class="tier-desc">Sentimento | Concorrencia &mdash; ideias para conteudo</div>
    </div>
    <div id="container-tier-3"></div>
  </div>

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
          document.getElementById('stat-ultima').textContent =
            fmtData(ue.data_execucao) + ' | ' + ue.itens_novos + ' novos (' + (ue.tipo_run || '?') + ')';
        } else {
          document.getElementById('stat-ultima').textContent = 'Aguardando primeira coleta';
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
        container.innerHTML = '<div class="empty"><p>Nenhuma oportunidade ' +
          (mostrarLidos ? '' : 'nao lida ') + 'no momento. ' +
          (tier === 1 ? 'Tier 1 e atualizado as 09:00 e 17:00.' :
           tier === 2 || tier === 3 ? 'Tier 2 e 3 sao atualizados ao meio-dia.' : '') +
          '</p></div>';
        return;
      }

      // Para tier 1: separar por etapa do concurso (antes_prova vs apos_prova)
      // Para outros: mostrar tudo junto
      if (tier === 1 || tier === 2) {
        const antes = itens.filter(i => i.etapa_concurso === 'antes_prova');
        const apos = itens.filter(i => i.etapa_concurso === 'apos_prova');
        const semEtapa = itens.filter(i => !i.etapa_concurso);

        let html = '';
        if (apos.length) {
          html += '<div class="phase-divider apos">Apos primeira etapa &mdash; ' + apos.length + '</div>';
          html += '<div class="cards-grid">' + apos.map(renderCard).join('') + '</div>';
        }
        if (antes.length) {
          html += '<div class="phase-divider antes">Antes da prova objetiva &mdash; ' + antes.length + '</div>';
          html += '<div class="cards-grid">' + antes.map(renderCard).join('') + '</div>';
        }
        if (semEtapa.length) {
          if (apos.length || antes.length) html += '<div class="phase-divider">Outros</div>';
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

      // Card de concurso: mostrar destaque com vagas e salario
      const isConcurso = (item.tier === 1 || item.tier === 2) && (item.vagas || item.salario || item.concurso);
      let concursoBlock = '';
      if (isConcurso && (item.vagas || item.salario)) {
        concursoBlock =
          '<div class="card-concurso-info">' +
            '<div class="info-block">' +
              '<div class="info-label">Vagas</div>' +
              '<div class="info-value">' + escapeHtml(item.vagas || 'nao informado') + '</div>' +
            '</div>' +
            '<div class="info-block">' +
              '<div class="info-label">Salario</div>' +
              '<div class="info-value">' + escapeHtml(item.salario || 'nao informado') + '</div>' +
            '</div>' +
          '</div>';
      }

      // Linha 1: nome do concurso + cargo (se tem concurso)
      let titleArea;
      if (item.concurso) {
        const cargoStr = item.cargo ? ' &mdash; ' + escapeHtml(item.cargo) : '';
        titleArea = '<div class="card-title">' + escapeHtml(item.concurso) + cargoStr + '</div>' +
                    '<div style="font-size:12px;color:var(--text-secondary);margin-top:-4px">' + escapeHtml(item.titulo) + '</div>';
      } else {
        titleArea = '<div class="card-title">' + escapeHtml(item.titulo) + '</div>';
      }

      // Badges
      const badges = [];
      if (item.estado) badges.push('<span class="badge estado">' + escapeHtml(item.estado) + '</span>');
      if (item.banca) badges.push('<span class="badge banca">' + escapeHtml(item.banca) + '</span>');
      if (item.fase_atual) badges.push('<span class="badge fase">' + escapeHtml(item.fase_atual) + '</span>');
      if (item.prazo_inscricao) badges.push('<span class="badge fase">Inscricao: ' + escapeHtml(item.prazo_inscricao) + '</span>');
      if (item.data_prova) badges.push('<span class="badge">Prova: ' + escapeHtml(item.data_prova) + '</span>');

      // Extras (campos especificos da categoria)
      let extrasBlock = '';
      if (item.extras && Object.keys(item.extras).length) {
        const extrasParts = [];
        for (const [k, v] of Object.entries(item.extras)) {
          if (!v) continue;
          if (k === 'citacao_candidato') {
            extrasParts.push('<div class="citacao">"' + escapeHtml(v) + '"</div>');
          } else {
            const labelMap = {
              'candidatos_estimados': 'Eliminados (estimado)',
              'fase_eliminacao': 'Fase',
              'tipo_irregularidade': 'Tipo',
              'questao_numero': 'Questao',
              'afetados_estimados': 'Afetados',
              'tribunal': 'Tribunal',
              'tema': 'Tema',
              'numero_processo': 'Processo',
              'tese': 'Tese',
              'concurso_mencionado': 'Concurso',
              'padrao_emocional': 'Padrao emocional',
              'escritorio_concorrente': 'Concorrente',
              'concurso_tema': 'Tema explorado',
              'gap_identificado': 'Gap identificado',
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
        if (data.erro) { toast('Erro: ' + data.erro); btn.disabled = false; btn.textContent = 'Coletar tudo'; return; }
        toast(data.mensagem, 10000);
        startPolling(btn, 'Coletar tudo');
      } catch (e) {
        toast('Erro');
        btn.disabled = false; btn.textContent = 'Coletar tudo';
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


seed_demo_se_vazio()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))
    app.run(host="0.0.0.0", port=port, debug=False)
