"""
╔══════════════════════════════════════════════════════════════╗
║          MEMÓRIA DAS CONVERSAS — memoria.py                  ║
║  Guarda o histórico de cada paciente para que o chatbot      ║
║  lembre o contexto da conversa (nome, caso clínico, etc.)    ║
╚══════════════════════════════════════════════════════════════╝
"""

from datetime import datetime, timedelta

# Dicionário em memória: { "numero_telefone": [ lista de mensagens ] }
# Nota: ao reiniciar o servidor, o histórico é perdido.
# Para persistência real, use um banco de dados (ex: Redis, SQLite).
_conversas: dict = {}

# Tempo máximo de inatividade antes de limpar o histórico (em horas)
HORAS_INATIVIDADE = 24

# Máximo de mensagens mantidas por conversa (evita contexto muito longo)
MAX_MENSAGENS = 20


def salvar_mensagem(numero: str, role: str, conteudo: str):
    """
    Salva uma mensagem no histórico da conversa do paciente.

    Parâmetros:
        numero  : número de telefone (identificador único do paciente)
        role    : "user" (paciente) ou "assistant" (chatbot)
        conteudo: texto da mensagem
    """
    if numero not in _conversas:
        _conversas[numero] = {
            "mensagens": [],
            "ultima_atividade": datetime.now()
        }

    _conversas[numero]["mensagens"].append({
        "role": role,
        "content": conteudo
    })
    _conversas[numero]["ultima_atividade"] = datetime.now()

    # Mantém apenas as últimas MAX_MENSAGENS para não sobrecarregar a IA
    if len(_conversas[numero]["mensagens"]) > MAX_MENSAGENS:
        _conversas[numero]["mensagens"] = _conversas[numero]["mensagens"][-MAX_MENSAGENS:]

    print(f"💾 Histórico de {numero}: {len(_conversas[numero]['mensagens'])} mensagens")


def obter_historico(numero: str) -> list:
    """
    Retorna o histórico de mensagens de um paciente.
    Se a conversa estiver inativa há muito tempo, limpa e começa do zero.

    Retorna:
        Lista de mensagens no formato [{"role": "...", "content": "..."}]
    """
    if numero not in _conversas:
        return []

    # Verifica inatividade
    ultima = _conversas[numero]["ultima_atividade"]
    if datetime.now() - ultima > timedelta(hours=HORAS_INATIVIDADE):
        print(f"🔄 Histórico de {numero} expirado. Iniciando nova conversa.")
        limpar_historico(numero)
        return []

    return _conversas[numero]["mensagens"]


def limpar_historico(numero: str):
    """
    Remove o histórico de um paciente (usado após inatividade ou encerramento).
    """
    if numero in _conversas:
        del _conversas[numero]
        print(f"🗑️ Histórico de {numero} removido.")


def total_conversas_ativas() -> int:
    """Retorna quantas conversas estão ativas no momento."""
    return len(_conversas)
