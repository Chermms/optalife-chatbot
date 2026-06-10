"""
╔══════════════════════════════════════════════════════════════╗
║          MEMÓRIA DAS CONVERSAS — memoria.py                  ║
║  Persiste o histórico em SQLite para sobreviver a            ║
║  reinicializações do servidor (Render worker timeout etc.)   ║
╚══════════════════════════════════════════════════════════════╝
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta, timezone

# ── Arquivo do banco de dados ──
DB_PATH = os.environ.get("DB_PATH", "/tmp/optalife_conversas.db")

# Tempo máximo de inatividade antes de limpar o histórico (em horas)
HORAS_INATIVIDADE = 24

# Máximo de mensagens mantidas por conversa
MAX_MENSAGENS = 20


# ─────────────────────────────────────────────
# INICIALIZA O BANCO NA PRIMEIRA EXECUÇÃO
# ─────────────────────────────────────────────
def _inicializar_banco():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversas (
                numero           TEXT PRIMARY KEY,
                mensagens        TEXT NOT NULL DEFAULT '[]',
                ultima_atividade TEXT NOT NULL
            )
        """)
        conn.commit()

_inicializar_banco()


# ─────────────────────────────────────────────
# SALVAR MENSAGEM
# ─────────────────────────────────────────────
def salvar_mensagem(numero: str, role: str, conteudo: str):
    """
    Salva uma mensagem no histórico persistido em SQLite.
    """
    mensagens = obter_historico(numero)

    mensagens.append({"role": role, "content": conteudo})

    # Mantém apenas as últimas MAX_MENSAGENS
    if len(mensagens) > MAX_MENSAGENS:
        mensagens = mensagens[-MAX_MENSAGENS:]

    BRT = timezone(timedelta(hours=-3))
    agora = datetime.now(BRT).isoformat()

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO conversas (numero, mensagens, ultima_atividade)
            VALUES (?, ?, ?)
            ON CONFLICT(numero) DO UPDATE SET
                mensagens        = excluded.mensagens,
                ultima_atividade = excluded.ultima_atividade
        """, (numero, json.dumps(mensagens, ensure_ascii=False), agora))
        conn.commit()

    print(f"💾 Histórico de {numero}: {len(mensagens)} mensagens")


# ─────────────────────────────────────────────
# OBTER HISTÓRICO
# ─────────────────────────────────────────────
def obter_historico(numero: str) -> list:
    """
    Retorna o histórico de mensagens do paciente.
    Limpa automaticamente se inativo há mais de HORAS_INATIVIDADE.
    """
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT mensagens, ultima_atividade FROM conversas WHERE numero = ?",
            (numero,)
        ).fetchone()

    if not row:
        return []

    mensagens_json, ultima_str = row

    # Verifica inatividade
    try:
        ultima = datetime.fromisoformat(ultima_str)
        # Garante que ultima seja tz-aware (registros antigos sem offset)
        if ultima.tzinfo is None:
            ultima = ultima.replace(tzinfo=timezone(timedelta(hours=-3)))
        if datetime.now(BRT) - ultima > timedelta(hours=HORAS_INATIVIDADE):
            print(f"🔄 Histórico de {numero} expirado. Iniciando nova conversa.")
            limpar_historico(numero)
            return []
    except Exception:
        pass

    try:
        return json.loads(mensagens_json)
    except Exception:
        return []


# ─────────────────────────────────────────────
# LIMPAR HISTÓRICO
# ─────────────────────────────────────────────
def limpar_historico(numero: str):
    """
    Remove o histórico de um paciente.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM conversas WHERE numero = ?", (numero,))
        conn.commit()
    print(f"🗑️ Histórico de {numero} removido.")


# ─────────────────────────────────────────────
# TOTAL DE CONVERSAS ATIVAS
# ─────────────────────────────────────────────
def total_conversas_ativas() -> int:
    """Retorna quantas conversas estão ativas no momento."""
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT COUNT(*) FROM conversas").fetchone()
    return row[0] if row else 0
