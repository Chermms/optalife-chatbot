"""
╔══════════════════════════════════════════════════════════════╗
║          MEMÓRIA DAS CONVERSAS — memoria.py                  ║
║  Persiste o histórico em PostgreSQL (Render Postgres) para   ║
║  sobreviver a reinicializações do worker e permitir acesso   ║
║  simultâneo do bot e do futuro painel de atendimento.        ║
╚══════════════════════════════════════════════════════════════╝
"""

import json
import os
from datetime import datetime, timedelta, timezone

import psycopg2
import psycopg2.extras
from psycopg2.pool import SimpleConnectionPool

# ── Conexão com o banco ──
# No Render, a variável DATABASE_URL é injetada automaticamente quando
# você vincula um banco Postgres ao serviço web. Em desenvolvimento local,
# defina-a manualmente no .env.
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL não definida. Configure a variável de ambiente "
        "apontando para o seu banco Render Postgres."
    )

# Pool de conexões — evita abrir/fechar conexão a cada chamada,
# o que é caro em PostgreSQL comparado ao SQLite local.
_pool = SimpleConnectionPool(minconn=1, maxconn=10, dsn=DATABASE_URL)

BRT = timezone(timedelta(hours=-3))

# Tempo máximo de inatividade antes de limpar o histórico (em horas)
HORAS_INATIVIDADE = 24

# Máximo de mensagens mantidas por conversa
MAX_MENSAGENS = 20


# ─────────────────────────────────────────────
# HELPERS DE CONEXÃO
# ─────────────────────────────────────────────
def _get_conn():
    return _pool.getconn()


def _put_conn(conn):
    _pool.putconn(conn)


# ─────────────────────────────────────────────
# INICIALIZA O BANCO NA PRIMEIRA EXECUÇÃO
# ─────────────────────────────────────────────
def _inicializar_banco():
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS conversas (
                    numero           TEXT PRIMARY KEY,
                    mensagens        JSONB NOT NULL DEFAULT '[]'::jsonb,
                    ultima_atividade TIMESTAMPTZ NOT NULL
                )
            """)
        conn.commit()
    finally:
        _put_conn(conn)

_inicializar_banco()


# ─────────────────────────────────────────────
# SALVAR MENSAGEM
# ─────────────────────────────────────────────
def salvar_mensagem(numero: str, role: str, conteudo: str):
    """
    Salva uma mensagem no histórico persistido em PostgreSQL.
    Mantém a mesma assinatura/comportamento da versão SQLite original.
    """
    mensagens = obter_historico(numero)

    mensagens.append({"role": role, "content": conteudo})

    # Mantém apenas as últimas MAX_MENSAGENS
    if len(mensagens) > MAX_MENSAGENS:
        mensagens = mensagens[-MAX_MENSAGENS:]

    agora = datetime.now(BRT)

    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO conversas (numero, mensagens, ultima_atividade)
                VALUES (%s, %s, %s)
                ON CONFLICT (numero) DO UPDATE SET
                    mensagens        = EXCLUDED.mensagens,
                    ultima_atividade = EXCLUDED.ultima_atividade
            """, (numero, json.dumps(mensagens, ensure_ascii=False), agora))
        conn.commit()
    finally:
        _put_conn(conn)

    print(f"💾 Histórico de {numero}: {len(mensagens)} mensagens")


# ─────────────────────────────────────────────
# OBTER HISTÓRICO
# ─────────────────────────────────────────────
def obter_historico(numero: str) -> list:
    """
    Retorna o histórico de mensagens do paciente.
    Limpa automaticamente se inativo há mais de HORAS_INATIVIDADE.
    """
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT mensagens, ultima_atividade FROM conversas WHERE numero = %s",
                (numero,)
            )
            row = cur.fetchone()
    finally:
        _put_conn(conn)

    if not row:
        return []

    mensagens_json, ultima = row

    # Verifica inatividade
    try:
        # psycopg2 já retorna um datetime tz-aware para TIMESTAMPTZ
        if ultima.tzinfo is None:
            ultima = ultima.replace(tzinfo=BRT)
        if datetime.now(BRT) - ultima > timedelta(hours=HORAS_INATIVIDADE):
            print(f"🔄 Histórico de {numero} expirado. Iniciando nova conversa.")
            limpar_historico(numero)
            return []
    except Exception:
        pass

    # JSONB já chega desserializado como list/dict do Python via psycopg2
    if isinstance(mensagens_json, str):
        try:
            return json.loads(mensagens_json)
        except Exception:
            return []
    return mensagens_json or []


# ─────────────────────────────────────────────
# LIMPAR HISTÓRICO
# ─────────────────────────────────────────────
def limpar_historico(numero: str):
    """
    Remove o histórico de um paciente.
    """
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM conversas WHERE numero = %s", (numero,))
        conn.commit()
    finally:
        _put_conn(conn)
    print(f"🗑️ Histórico de {numero} removido.")


# ─────────────────────────────────────────────
# TOTAL DE CONVERSAS ATIVAS
# ─────────────────────────────────────────────
def total_conversas_ativas() -> int:
    """Retorna quantas conversas estão ativas no momento."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM conversas")
            row = cur.fetchone()
    finally:
        _put_conn(conn)
    return row[0] if row else 0
