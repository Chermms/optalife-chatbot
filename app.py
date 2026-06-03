"""
╔══════════════════════════════════════════════════════════════╗
║          CHATBOT OPTALIFE — WhatsApp + Groq AI               ║
║          Arquivo principal: app.py                           ║
╚══════════════════════════════════════════════════════════════╝

Como funciona:
1. O WhatsApp envia mensagens para este servidor via Webhook
2. O servidor processa e envia para a IA (Groq)
3. A IA responde com base no script da OptaLife
4. O servidor devolve a resposta ao WhatsApp
"""

import os
import json
import requests
from flask import Flask, request, jsonify
from groq_client import obter_resposta_ia
from memoria import salvar_mensagem, obter_historico, limpar_historico

app = Flask(__name__)

# ─────────────────────────────────────────────
# CONFIGURAÇÕES (lidas do arquivo .env)
# ─────────────────────────────────────────────
WHATSAPP_TOKEN   = os.environ.get("WHATSAPP_TOKEN")    # Token da API do WhatsApp
VERIFY_TOKEN     = os.environ.get("VERIFY_TOKEN")      # Token de verificação do Webhook
PHONE_NUMBER_ID  = os.environ.get("PHONE_NUMBER_ID")   # ID do número WhatsApp Business


# ─────────────────────────────────────────────
# ROTA DE VERIFICAÇÃO DO WEBHOOK (Meta exige)
# ─────────────────────────────────────────────
@app.route("/webhook", methods=["GET"])
def verificar_webhook():
    """
    A Meta verifica se o servidor é válido enviando um GET com um token.
    Precisamos responder com o 'hub.challenge' para confirmar.
    """
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verificado com sucesso!")
        return challenge, 200
    else:
        print("❌ Token de verificação inválido.")
        return "Token inválido", 403


# ─────────────────────────────────────────────
# ROTA PRINCIPAL: RECEBE MENSAGENS DO WHATSAPP
# ─────────────────────────────────────────────
@app.route("/webhook", methods=["POST"])
def receber_mensagem():
    """
    Toda mensagem enviada ao número WhatsApp da OptaLife
    chega aqui. Processamos e respondemos automaticamente.
    """
    data = request.get_json()

    try:
        # Navega pela estrutura JSON do WhatsApp
        entry    = data["entry"][0]
        changes  = entry["changes"][0]
        value    = changes["value"]

        # Ignora se não houver mensagem (ex: notificações de status)
        if "messages" not in value:
            return jsonify({"status": "sem mensagem"}), 200

        mensagem_obj = value["messages"][0]
        numero       = mensagem_obj["from"]          # Número de quem enviou
        tipo         = mensagem_obj["type"]          # text, audio, image, etc.

        # Por enquanto processamos apenas texto
        if tipo != "text":
            enviar_whatsapp(numero, "Olá! No momento processo apenas mensagens de texto. Por favor, descreva sua dúvida em texto e terei prazer em ajudá-lo(a). 😊")
            return jsonify({"status": "tipo não suportado"}), 200

        texto_recebido = mensagem_obj["text"]["body"]
        print(f"📩 Mensagem de {numero}: {texto_recebido}")

        # Salva a mensagem do usuário no histórico
        salvar_mensagem(numero, "user", texto_recebido)

        # Obtém o histórico da conversa para contexto
        historico = obter_historico(numero)

        # Envia para a IA e obtém resposta
        resposta = obter_resposta_ia(historico)

        # Salva a resposta da IA no histórico
        salvar_mensagem(numero, "assistant", resposta)

        # Envia a resposta pelo WhatsApp
        enviar_whatsapp(numero, resposta)

        print(f"📤 Resposta enviada para {numero}: {resposta[:80]}...")
        return jsonify({"status": "mensagem processada"}), 200

    except Exception as e:
        print(f"⚠️ Erro ao processar mensagem: {e}")
        return jsonify({"status": "erro", "detalhe": str(e)}), 500


# ─────────────────────────────────────────────
# FUNÇÃO: ENVIAR MENSAGEM PELO WHATSAPP
# ─────────────────────────────────────────────
def enviar_whatsapp(numero_destino: str, texto: str):
    """
    Envia uma mensagem de texto para um número via API do WhatsApp Business.
    """
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": numero_destino,
        "type": "text",
        "text": {"body": texto}
    }

    resposta = requests.post(url, headers=headers, json=payload)

    if resposta.status_code != 200:
        print(f"⚠️ Erro ao enviar mensagem: {resposta.text}")


# ─────────────────────────────────────────────
# INICIALIZA O SERVIDOR
# ─────────────────────────────────────────────
if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 5000))
    print(f"🚀 Servidor OptaLife iniciado na porta {porta}")
    app.run(host="0.0.0.0", port=porta, debug=False)
