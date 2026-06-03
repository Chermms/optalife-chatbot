"""
╔══════════════════════════════════════════════════════════════╗
║          CHATBOT OPTALIFE — WhatsApp + Groq AI               ║
║          Arquivo principal: app.py                           ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import requests
from flask import Flask, request, jsonify
from groq_client import obter_resposta_ia
from memoria import salvar_mensagem, obter_historico

app = Flask(__name__)

WHATSAPP_TOKEN  = os.environ.get("WHATSAPP_TOKEN")
VERIFY_TOKEN    = os.environ.get("VERIFY_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")


# ─────────────────────────────────────────────
# ROTA RAIZ — evita 404 e mantém servidor ativo
# ─────────────────────────────────────────────
@app.route("/", methods=["GET", "HEAD"])
def home():
    return "OptaLife Chatbot está no ar! ✅", 200


# ─────────────────────────────────────────────
# VERIFICAÇÃO DO WEBHOOK (Meta)
# ─────────────────────────────────────────────
@app.route("/webhook", methods=["GET"])
def verificar_webhook():
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
# RECEBE MENSAGENS DO WHATSAPP
# ─────────────────────────────────────────────
@app.route("/webhook", methods=["POST"])
def receber_mensagem():
    data = request.get_json()

    try:
        entry    = data["entry"][0]
        changes  = entry["changes"][0]
        value    = changes["value"]

        if "messages" not in value:
            return jsonify({"status": "sem mensagem"}), 200

        mensagem_obj   = value["messages"][0]
        numero         = mensagem_obj["from"]
        tipo           = mensagem_obj["type"]

        # Ignora mensagens duplicadas (Meta pode reenviar)
        message_id = mensagem_obj.get("id", "")
        print(f"📩 [{message_id}] Mensagem de {numero} ({tipo})")

        if tipo != "text":
            enviar_whatsapp(numero,
                "Olá! No momento processo apenas mensagens de texto. "
                "Por favor, descreva sua dúvida em texto e terei prazer em ajudá-lo(a). 😊"
            )
            return jsonify({"status": "tipo não suportado"}), 200

        texto_recebido = mensagem_obj["text"]["body"]
        print(f"💬 Conteúdo: {texto_recebido}")

        salvar_mensagem(numero, "user", texto_recebido)
        historico = obter_historico(numero)
        resposta  = obter_resposta_ia(historico)
        salvar_mensagem(numero, "assistant", resposta)

        enviar_whatsapp(numero, resposta)
        print(f"📤 Resposta enviada: {resposta[:80]}...")

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print(f"⚠️ Erro: {e}")
        return jsonify({"status": "erro", "detalhe": str(e)}), 500


# ─────────────────────────────────────────────
# ENVIA MENSAGEM PELO WHATSAPP
# ─────────────────────────────────────────────
def enviar_whatsapp(numero_destino: str, texto: str):
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
        print(f"⚠️ Erro ao enviar: {resposta.text}")


# ─────────────────────────────────────────────
# INICIA O SERVIDOR
# ─────────────────────────────────────────────
if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 10000))
    print(f"🚀 Servidor OptaLife iniciado na porta {porta}")
    app.run(host="0.0.0.0", port=porta, debug=False)
