"""
╔══════════════════════════════════════════════════════════════╗
║          TRIAGENS ESTRUTURADAS — triagens.py                 ║
║  Persiste os dados extraídos da triagem (nome, telefone,     ║
║  especialidade, convênio, descrição) em PostgreSQL.          ║
║  Essa tabela é a fonte de dados do futuro painel interno      ║
║  de atendimento da OptaLife.                                  ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
from datetime import datetime, timedelta, timezone

import psycopg2
import psycopg2.extras
from psycopg2.pool import SimpleConnectionPool

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL não definida. Configure a variável de ambiente "
        "apontando para o seu banco Render Postgres."
    )

_pool = SimpleConnectionPool(minconn=1, maxconn=10, dsn=DATABASE_URL)

BRT = timezone(timedelta(hours=-3))


def _get_conn():
    return _pool.getconn()


def _put_conn(conn):
    _pool.putconn(conn)


# ─────────────────────────────────────────────
# INICIALIZA A TABELA NA PRIMEIRA EXECUÇÃO
# ─────────────────────────────────────────────
def _inicializar_banco():
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS triagens (
                    id            SERIAL PRIMARY KEY,
                    numero        TEXT NOT NULL,
                    nome          TEXT,
                    telefone      TEXT,
                    email         TEXT,
                    especialidade TEXT,
                    convenio      TEXT,
                    descricao     TEXT,
                    origem        TEXT NOT NULL DEFAULT 'whatsapp',
                    status        TEXT NOT NULL DEFAULT 'novo',
                    criado_em     TIMESTAMPTZ NOT NULL DEFAULT now()
                )
            """)
            # Índices para as consultas mais comuns do painel
            cur.execute("CREATE INDEX IF NOT EXISTS idx_triagens_numero ON triagens (numero)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_triagens_status ON triagens (status)")
        conn.commit()
    finally:
        _put_conn(conn)

_inicializar_banco()


# ─────────────────────────────────────────────
# SALVAR TRIAGEM CONCLUÍDA
# ─────────────────────────────────────────────
def salvar_triagem(numero: str, dados: dict, origem: str = "whatsapp") -> int:
    """
    Persiste uma triagem concluída (vinda do WhatsApp via groq_client.extrair_dados_triagem
    ou do formulário do site). Retorna o id do registro criado.

    `dados` espera as chaves: nome, telefone, especialidade, convenio, descricao
    (e opcionalmente email, usado pelo formulário do site).
    """
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO triagens
                    (numero, nome, telefone, email, especialidade, convenio, descricao, origem, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'novo')
                RETURNING id
            """, (
                numero,
                dados.get("nome"),
                dados.get("telefone"),
                dados.get("email"),
                dados.get("especialidade"),
                dados.get("convenio"),
                dados.get("descricao"),
                origem,
            ))
            triagem_id = cur.fetchone()[0]
        conn.commit()
    finally:
        _put_conn(conn)

    print(f"📋 Triagem #{triagem_id} salva para {numero} (origem: {origem})")
    return triagem_id


# ─────────────────────────────────────────────
# LISTAR TRIAGENS (uso futuro do painel)
# ─────────────────────────────────────────────
def listar_triagens(status: str = None, limite: int = 50) -> list:
    """
    Lista triagens, mais recentes primeiro. Filtra por status se informado
    (ex: 'novo', 'em_atendimento', 'agendado', 'concluido').
    """
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if status:
                cur.execute("""
                    SELECT * FROM triagens
                    WHERE status = %s
                    ORDER BY criado_em DESC
                    LIMIT %s
                """, (status, limite))
            else:
                cur.execute("""
                    SELECT * FROM triagens
                    ORDER BY criado_em DESC
                    LIMIT %s
                """, (limite,))
            rows = cur.fetchall()
    finally:
        _put_conn(conn)
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────
# ATUALIZAR STATUS DE UMA TRIAGEM
# ─────────────────────────────────────────────
def atualizar_status_triagem(triagem_id: int, novo_status: str):
    """
    Atualiza o status de uma triagem (ex: 'novo' -> 'em_atendimento' -> 'agendado').
    """
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE triagens SET status = %s WHERE id = %s",
                (novo_status, triagem_id)
            )
        conn.commit()
    finally:
        _put_conn(conn)
    print(f"🔄 Triagem #{triagem_id} atualizada para status '{novo_status}'")
