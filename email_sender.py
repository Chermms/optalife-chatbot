"""
╔══════════════════════════════════════════════════════════════╗
║          EMAIL SENDER — email_sender.py                      ║
║  Envia a triagem do paciente para contato@optalife.com.br    ║
║  Usa Resend API (HTTP) — compatível com Render               ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import requests
from datetime import datetime

RESEND_API_KEY     = os.environ.get("RESEND_API_KEY")
EMAIL_REMETENTE    = os.environ.get("EMAIL_REMETENTE", "sofia@optalife.com.br")
EMAIL_DESTINATARIO = "contato@optalife.com.br"


def enviar_triagem_por_email(triagem: dict):
    """
    Envia um e-mail HTML formatado com os dados da triagem via Resend API.
    """
    # ── Diagnóstico de configuração ──
    print(f"📧 RESEND_API_KEY configurada: {'✅ Sim' if RESEND_API_KEY else '❌ NÃO — variável ausente!'}")
    print(f"📧 EMAIL_REMETENTE: {EMAIL_REMETENTE}")
    print(f"📧 Destinatário: {EMAIL_DESTINATARIO}")

    if not RESEND_API_KEY:
        print("⚠️ E-mail NÃO enviado: RESEND_API_KEY não configurada no Render.")
        return False

    try:
        agora         = datetime.now().strftime("%d/%m/%Y às %H:%M")
        nome          = triagem.get("nome", "Não informado")
        telefone      = triagem.get("telefone", triagem.get("numero", "Não informado"))
        especialidade = triagem.get("especialidade", "Não informado")
        convenio      = triagem.get("convenio", "Não informado")
        descricao     = triagem.get("descricao", "Não informado")
        numero_wa     = triagem.get("numero", "Não informado")

        assunto = f"🩺 Nova Triagem OptaLife — {nome} ({agora})"

        corpo_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: auto;">

          <div style="background-color: #0a5c8a; padding: 20px; border-radius: 8px 8px 0 0;">
            <h2 style="color: white; margin: 0;">🩺 Nova Triagem — OptaLife</h2>
            <p style="color: #cce6f7; margin: 4px 0 0 0;">Registrada em {agora}</p>
          </div>

          <div style="background-color: #f4f8fb; padding: 24px; border: 1px solid #d0e4f0;">
            <h3 style="color: #0a5c8a; border-bottom: 1px solid #cce; padding-bottom: 6px;">
              Dados do Paciente
            </h3>
            <table style="width: 100%; border-collapse: collapse;">
              <tr>
                <td style="padding: 8px; font-weight: bold; width: 40%;">Nome completo:</td>
                <td style="padding: 8px;">{nome}</td>
              </tr>
              <tr style="background:#e8f3fb;">
                <td style="padding: 8px; font-weight: bold;">Telefone:</td>
                <td style="padding: 8px;">{telefone}</td>
              </tr>
              <tr>
                <td style="padding: 8px; font-weight: bold;">WhatsApp (origem):</td>
                <td style="padding: 8px;">+{numero_wa}</td>
              </tr>
            </table>

            <div style="text-align:center;margin-top:20px;margin-bottom:8px;">
              <a href="https://wa.me/{numero_wa}" style="display:inline-block;background:#25D366;color:white;font-size:16px;font-weight:bold;padding:14px 32px;border-radius:8px;text-decoration:none;">
                💬 Abrir conversa no WhatsApp
              </a>
            </div>

            <table style="width: 100%; border-collapse: collapse; margin-top: 16px;">
              <tr style="background:#e8f3fb;">
                <td style="padding: 8px; font-weight: bold;">Especialidade / Cirurgia:</td>
                <td style="padding: 8px;">{especialidade}</td>
              </tr>
              <tr>
                <td style="padding: 8px; font-weight: bold;">Convênio:</td>
                <td style="padding: 8px;">{convenio}</td>
              </tr>
            </table>

            <h3 style="color: #0a5c8a; border-bottom: 1px solid #cce; padding-bottom: 6px; margin-top: 24px;">
              Descrição do Caso Clínico
            </h3>
            <p style="background: white; padding: 12px; border-left: 4px solid #0a5c8a;
                      border-radius: 4px; line-height: 1.6;">
              {descricao}
            </p>
          </div>

          <div style="background-color: #0a5c8a; padding: 14px; border-radius: 0 0 8px 8px; text-align: center;">
            <p style="color: white; margin: 0; font-size: 13px;">
              OptaLife — Soluções em Cirurgias &nbsp;|&nbsp;
              <a href="https://www.optalife.com.br" style="color: #cce6f7;">www.optalife.com.br</a>
            </p>
          </div>

        </body>
        </html>
        """

        print(f"📧 Enviando e-mail para {EMAIL_DESTINATARIO}...")

        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from": f"Sofia OptaLife <{EMAIL_REMETENTE}>",
                "to": [EMAIL_DESTINATARIO],
                "subject": assunto,
                "html": corpo_html
            },
            timeout=15
        )

        print(f"📧 Resposta Resend: status={response.status_code} | body={response.text}")

        if response.status_code in (200, 201):
            print(f"✅ E-mail enviado com sucesso — Paciente: {nome}")
            return True
        else:
            print(f"⚠️ Resend recusou o envio: {response.status_code} — {response.text}")
            return False

    except Exception as e:
        print(f"⚠️ Exceção ao enviar e-mail: {type(e).__name__}: {e}")
        return False
