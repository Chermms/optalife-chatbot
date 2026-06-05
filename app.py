"""
╔══════════════════════════════════════════════════════════════╗
║          CHATBOT OPTALIFE — WhatsApp + Groq AI               ║
║          Arquivo principal: app.py                           ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import requests
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq_client import obter_resposta_ia, triagem_foi_concluida, extrair_dados_triagem
from memoria import salvar_mensagem, obter_historico
from email_sender import enviar_triagem_por_email

app = Flask(__name__)
CORS(app, origins=["https://optalife.com.br", "https://www.optalife.com.br"])

WHATSAPP_TOKEN   = os.environ.get("WHATSAPP_TOKEN")
VERIFY_TOKEN     = os.environ.get("VERIFY_TOKEN")
PHONE_NUMBER_ID  = os.environ.get("PHONE_NUMBER_ID")
ATENDENTE_NUMERO = os.environ.get("ATENDENTE_NUMERO", "5521994404545")  # Atendente OptaLife


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
# DETECTA SE CLIENTE QUER ATENDENTE HUMANO
# ─────────────────────────────────────────────
def cliente_quer_atendente(texto: str) -> bool:
    palavras_chave = [
        "atendente", "humano", "pessoa real", "falar com alguém",
        "falar com uma pessoa", "quero falar com alguém",
        "atendimento humano", "falar com atendente",
        "falar com um humano", 
         "preciso de ajuda humana",
        "me passa para um atendente", "me transfere"
    ]
    texto_lower = texto.lower()
    return any(palavra in texto_lower for palavra in palavras_chave)


# ─────────────────────────────────────────────
# NOTIFICA A ATENDENTE ISABELA NO WHATSAPP
# ─────────────────────────────────────────────
def notificar_atendente(numero_cliente: str, texto_cliente: str, triagem: dict = None):
    """Notifica o atendente com os dados do paciente e triagem se disponível."""
    linhas_triagem = ""
    if triagem:
        nome         = triagem.get("nome", "Não informado")
        telefone     = triagem.get("telefone", "Não informado")
        especialidade = triagem.get("especialidade", "Não informado")
        convenio     = triagem.get("convenio", "Não informado")
        descricao    = triagem.get("descricao", "Não informado")
        linhas_triagem = (
            f"\n📋 *Triagem registrada:*\n"
            f"👤 *Nome:* {nome}\n"
            f"📞 *Telefone:* {telefone}\n"
            f"🩺 *Especialidade:* {especialidade}\n"
            f"💳 *Convênio:* {convenio}\n"
            f"📝 *Caso clínico:* {descricao}\n"
        )

    mensagem = (
        f"🔔 *Novo paciente aguardando atendimento!*\n\n"
        f"📱 *Número:* +{numero_cliente}\n"
        f"🔗 *Abrir conversa:* https://wa.me/{numero_cliente}\n"
        f"💬 *Última mensagem:* {texto_cliente}"
        f"{linhas_triagem}\n"
        f"Por favor, entre em contato com o(a) paciente. 💙"
    )
    enviar_whatsapp(ATENDENTE_NUMERO, mensagem)
    print(f"📣 Atendente notificada — paciente: {numero_cliente} → {ATENDENTE_NUMERO}")


# ─────────────────────────────────────────────
# DISPARA E-MAIL EM THREAD SEPARADA
# (evita timeout do Gunicorn)
# ─────────────────────────────────────────────
def disparar_email_async(historico: list, numero: str):
    """Extrai dados da triagem e envia e-mail em background."""
    try:
        print(f"📧 [thread] Extraindo dados da triagem de {numero}...")
        dados_triagem = extrair_dados_triagem(historico)
        dados_triagem["numero"] = numero
        enviar_triagem_por_email(dados_triagem)
    except Exception as e:
        print(f"⚠️ [thread] Erro ao enviar e-mail: {e}")


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

        mensagem_obj = value["messages"][0]
        numero       = mensagem_obj["from"]
        tipo         = mensagem_obj["type"]

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

        # ── Verifica se o paciente quer falar com atendente humano ──
        if cliente_quer_atendente(texto_recebido):
            # Tenta extrair triagem do histórico se já foi feita
            historico_atual = obter_historico(numero)
            triagem = None
            if historico_atual:
                try:
                    triagem = extrair_dados_triagem(historico_atual)
                except Exception:
                    triagem = None

            notificar_atendente(numero, texto_recebido, triagem)
            enviar_whatsapp(numero,
                "Claro! Vou chamar um(a) de nossos atendentes agora. 💙\n\n"
                "Em breve ele(a) entrará em contato com você diretamente.\n\n"
                "Caso prefira, você pode iniciar a conversa diretamente:\n"
                "🔗 https://wa.me/5521994404545\n\n"
                "Ou ligue para um dos nossos números de atendimento:\n"
                "(21) 96643-9937. ✅ ou (21) 99440-4545. ✅"
            )
            return jsonify({"status": "encaminhado para atendente"}), 200

        # ── Fluxo normal com IA ──
        salvar_mensagem(numero, "user", texto_recebido)
        historico = obter_historico(numero)
        resposta  = obter_resposta_ia(historico)
        salvar_mensagem(numero, "assistant", resposta)

        # ── Verifica se a triagem foi concluída ──
        if triagem_foi_concluida(resposta):
            print(f"📋 Triagem concluída para {numero}. Disparando e-mail em background...")

            # Busca histórico completo incluindo a resposta final da Sofia
            historico_completo = obter_historico(numero)

            # ✅ Roda em thread separada — não trava o webhook
            t = threading.Thread(
                target=disparar_email_async,
                args=(historico_completo, numero),
                daemon=True
            )
            t.start()

            # Remove o marcador antes de enviar a resposta ao paciente
            resposta = resposta.replace("##TRIAGEM_CONCLUIDA##", "").strip()

        enviar_whatsapp(numero, resposta)
        print(f"📤 Resposta enviada: {resposta[:80]}...")

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print(f"⚠️ Erro: {e}")
        return jsonify({"status": "erro", "detalhe": str(e)}), 500


# ─────────────────────────────────────────────
# RECEBE TRIAGEM DO SITE E ENVIA POR E-MAIL
# ─────────────────────────────────────────────
@app.route("/triagem", methods=["POST"])
def receber_triagem_site():
    """Recebe dados do formulário do site e envia e-mail para contato@optalife.com.br."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "erro", "mensagem": "Dados inválidos"}), 400

        from datetime import datetime
        import requests as req

        nome         = data.get("nome", "Não informado")
        telefone     = data.get("telefone", "Não informado")
        email        = data.get("email", "Não informado")
        cirurgia     = data.get("cirurgia", "Não informado")
        convenio     = data.get("convenio", "Não informado")
        descricao    = data.get("descricao", "Não informado")
        origem       = data.get("origem", "Site")
        agora        = datetime.now().strftime("%d/%m/%Y às %H:%M")

        corpo_html = f"""
        <html><body style="font-family:Arial,sans-serif;color:#333;max-width:600px;margin:auto;">
          <div style="background:#0a5c8a;padding:20px;border-radius:8px 8px 0 0;">
            <h2 style="color:white;margin:0;">🩺 Nova Triagem — OptaLife</h2>
            <p style="color:#cce6f7;margin:4px 0 0 0;">Via {origem} — {agora}</p>
          </div>
          <div style="background:#f4f8fb;padding:24px;border:1px solid #d0e4f0;">
            <h3 style="color:#0a5c8a;border-bottom:1px solid #cce;padding-bottom:6px;">Dados do Paciente</h3>
            <table style="width:100%;border-collapse:collapse;">
              <tr><td style="padding:8px;font-weight:bold;width:40%;">Nome completo:</td><td style="padding:8px;">{nome}</td></tr>
              <tr style="background:#e8f3fb;"><td style="padding:8px;font-weight:bold;">Telefone:</td><td style="padding:8px;">{telefone}</td></tr>
              <tr><td style="padding:8px;font-weight:bold;">E-mail:</td><td style="padding:8px;">{email}</td></tr>
              <tr style="background:#e8f3fb;"><td style="padding:8px;font-weight:bold;">Especialidade / Cirurgia:</td><td style="padding:8px;">{cirurgia}</td></tr>
              <tr><td style="padding:8px;font-weight:bold;">Convênio:</td><td style="padding:8px;">{convenio}</td></tr>
            </table>
            <h3 style="color:#0a5c8a;border-bottom:1px solid #cce;padding-bottom:6px;margin-top:24px;">Descrição do Caso Clínico</h3>
            <p style="background:white;padding:12px;border-left:4px solid #0a5c8a;border-radius:4px;line-height:1.6;">{descricao}</p>
          </div>
          <div style="background:#0a5c8a;padding:14px;border-radius:0 0 8px 8px;text-align:center;">
            <p style="color:white;margin:0;font-size:13px;">OptaLife — Soluções em Cirurgias | <a href="https://www.optalife.com.br" style="color:#cce6f7;">www.optalife.com.br</a></p>
          </div>
        </body></html>
        """

        resend_key = os.environ.get("RESEND_API_KEY")
        remetente  = os.environ.get("EMAIL_REMETENTE", "contato@optalife.com.br")

        response = req.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {resend_key}", "Content-Type": "application/json"},
            json={
                "from": f"Site OptaLife <{remetente}>",
                "to": ["contato@optalife.com.br"],
                "subject": f"🩺 Nova Triagem pelo Site — {nome}",
                "html": corpo_html
            },
            timeout=15
        )

        if response.status_code in (200, 201):
            print(f"✅ Triagem do site enviada — {nome}")
            return jsonify({"status": "ok"}), 200
        else:
            print(f"⚠️ Erro Resend: {response.text}")
            return jsonify({"status": "erro"}), 500

    except Exception as e:
        print(f"⚠️ Erro na triagem do site: {e}")
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
