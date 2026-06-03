"""
╔══════════════════════════════════════════════════════════════╗
║          EMAIL SENDER — email_sender.py                      ║
║  Envia a triagem do paciente para contato@optalife.com.br    ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ── Configurações de e-mail (via variáveis de ambiente) ──
EMAIL_REMETENTE = os.environ.get("EMAIL_REMETENTE")       # ex: bot@optalife.com.br
EMAIL_SENHA     = os.environ.get("EMAIL_SENHA")           # senha do e-mail ou App Password
EMAIL_DESTINATARIO = "contato@optalife.com.br"
SMTP_HOST       = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT       = int(os.environ.get("SMTP_PORT", 587))


def enviar_triagem_por_email(triagem: dict):
    """
    Envia um e-mail formatado com os dados da triagem do paciente.

    Parâmetros:
        triagem: dicionário com os dados coletados, ex:
        {
            "numero": "5521999999999",
            "nome": "João Silva",
            "telefone": "(21) 99999-9999",
            "especialidade": "Cirurgia da Coluna",
            "convenio": "Unimed",
            "descricao": "Dor lombar há 6 meses...",
            "historico_resumido": "..."   # opcional
        }
    """
    try:
        agora = datetime.now().strftime("%d/%m/%Y às %H:%M")

        nome         = triagem.get("nome", "Não informado")
        telefone     = triagem.get("telefone", triagem.get("numero", "Não informado"))
        especialidade = triagem.get("especialidade", "Não informado")
        convenio     = triagem.get("convenio", "Não informado")
        descricao    = triagem.get("descricao", "Não informado")
        numero_wa    = triagem.get("numero", "Não informado")
        historico    = triagem.get("historico_resumido", "")

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

            {"<h3 style='color:#0a5c8a;border-bottom:1px solid #cce;padding-bottom:6px;margin-top:24px;'>Histórico da Conversa</h3><pre style='background:white;padding:12px;border-radius:4px;font-size:13px;white-space:pre-wrap;'>" + historico + "</pre>" if historico else ""}

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

        msg = MIMEMultipart("alternative")
        msg["Subject"] = assunto
        msg["From"]    = EMAIL_REMETENTE
        msg["To"]      = EMAIL_DESTINATARIO
        msg.attach(MIMEText(corpo_html, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as servidor:
            servidor.starttls()
            servidor.login(EMAIL_REMETENTE, EMAIL_SENHA)
            servidor.sendmail(EMAIL_REMETENTE, EMAIL_DESTINATARIO, msg.as_string())

        print(f"✅ E-mail de triagem enviado para {EMAIL_DESTINATARIO} — Paciente: {nome}")
        return True

    except Exception as e:
        print(f"⚠️ Erro ao enviar e-mail de triagem: {e}")
        return False
