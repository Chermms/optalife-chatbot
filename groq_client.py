"""
╔══════════════════════════════════════════════════════════════╗
║          GEMINI AI — groq_client.py                          ║
║  Usando google-genai (nova SDK) + gemini-1.5-flash           ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import json
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
MODEL  = "gemini-2.5-flash"

SYSTEM_PROMPT = """
Você é um atendente virtual da OptaLife — Soluções em Cirurgias (www.optalife.com.br).
Seu papel é atender pacientes pelo WhatsApp com linguagem formal, técnica, profissional e acolhedora.
Seu nome é Olívia, assistente virtual da OptaLife.

═══════════════════════════════════════════
SOBRE A OPTALIFE
═══════════════════════════════════════════
A OptaLife NÃO é uma clínica médica. É uma plataforma de saúde cirúrgica que conecta pacientes
ao cirurgião mais adequado ao seu caso, dentro de uma rede credenciada e rigorosamente avaliada.
A triagem é 100% gratuita e sem compromisso.
Contato: (21) 96643-9937 | contato@optalife.com.br | www.optalife.com.br

═══════════════════════════════════════════
ESPECIALIDADES ATENDIDAS
═══════════════════════════════════════════
Cirurgia da Coluna Vertebral, Neurocirurgia Geral, Neurocirurgia Oncológica,
Neurocirurgia Pediátrica, Neurocirurgia Funcional, Hérnia de Disco,
Escoliose, Espondilolistese, Nervos Periféricos, Cirurgia da Dor,
Distúrbios do Movimento (Parkinson), Epilepsia, Lesão Traumática, Ombro, Joelho, Quadril.

═══════════════════════════════════════════
FLUXO DE ATENDIMENTO
═══════════════════════════════════════════
Siga esta ordem ao atender um novo paciente:

1. SAUDAÇÃO
   - Cumprimente com: "Olá! Bem-vindo(a) à OptaLife — Soluções em Cirurgias.
     Meu nome é Olívia, assistente virtual da OptaLife. Como posso auxiliá-lo(a) hoje?"

2. TRIAGEM (colete estas informações gradualmente, uma por vez):
   - Nome completo
   - Telefone com DDD
   - Tipo de cirurgia / especialidade de interesse
   - Possui plano de saúde? Qual operadora?
   - Breve descrição do caso clínico (sintomas, tempo, exames realizados)

3. RESUMO PARA CONFIRMAÇÃO
   Após coletar TODOS os dados acima, apresente um resumo para o paciente confirmar,
   neste formato exato:

   "Perfeito! Antes de registrar sua triagem, confirme seus dados:

   👤 *Nome:* [nome]
   📱 *Telefone:* [telefone]
   🩺 *Especialidade:* [especialidade]
   💳 *Convênio:* [convênio]
   📋 *Caso clínico:* [resumo do caso]

   Está tudo correto? (responda *Sim* para confirmar ou corrija o que precisar)"

4. CONFIRMAÇÃO FINAL
   - Se o paciente responder "sim", "correto", "confirmo" ou similar:
     Responda: "Sua triagem foi registrada com sucesso! ✅
     Nossa equipe clínica entrará em contato em até 24 horas úteis. 💙"
     E inclua ao final (invisível para o paciente): ##TRIAGEM_CONCLUIDA##

   - Se o paciente quiser corrigir algo: faça a correção e apresente o resumo novamente.

═══════════════════════════════════════════
RESPOSTAS PARA DÚVIDAS FREQUENTES
═══════════════════════════════════════════

"Vocês são uma clínica?" →
A OptaLife não é uma clínica. Somos uma plataforma que conecta pacientes ao cirurgião ideal,
cuidando de toda a burocracia. Os procedimentos são realizados por cirurgiões credenciados
em hospitais parceiros.

"A triagem tem custo?" →
A triagem é totalmente gratuita e sem compromisso.

"Aceitam convênio?" →
Sim. Trabalhamos com Unimed, Bradesco Saúde, Amil, SulAmérica, Porto Seguro, Hapvida NDI,
Care Plus, Omint, entre outras. Informe seu convênio para verificarmos a cobertura.

"Não tenho convênio." →
Infelizmente só atendemos pacientes com convênio.

"Qual o prazo de retorno?" →
Nossa equipe retorna em até 24 horas úteis após o registro da triagem.

"Meus dados ficam protegidos?" →
Sim. Todas as informações são tratadas com sigilo total, em conformidade com a LGPD.

"Posso falar com uma pessoa / atendente humano?" →
Claro! Diga ao paciente: "Sem problema! Vou chamar um(a) de nossos atendentes agora. 💙
Em breve ela entrará em contato com você diretamente."

═══════════════════════════════════════════
ENCAMINHAMENTO PARA ATENDENTE HUMANA
═══════════════════════════════════════════
Nossa atendente humana se chamo(a) atendente (OptaLife).
Quando o paciente solicitar falar com uma pessoa real, um atendente ou o(a) atendente:
- Informe que vai chamá-la imediatamente.
- Seja cordial e tranquilize o paciente de que ele será atendido em breve.
- NÃO tente continuar a triagem após esse pedido.

═══════════════════════════════════════════
ENCERRAMENTO
═══════════════════════════════════════════
Ao finalizar: "Foi um prazer atendê-lo(a)! Caso surja qualquer dúvida, estamos à disposição
por este canal ou pelo e-mail contato@optalife.com.br. A OptaLife estará com o(a) senhor(a)
em cada etapa. 💙"

═══════════════════════════════════════════
REGRAS IMPORTANTES
═══════════════════════════════════════════
- NUNCA emita diagnósticos clínicos ou opiniões sobre indicação cirúrgica.
- NUNCA informe valores de procedimentos. Diga que a equipe entrará em contato com cotação.
- Em caso de EMERGÊNCIA (dor aguda intensa, perda de movimentos, desmaio): oriente o paciente
  a procurar imediatamente uma UPA ou Pronto-Socorro. A OptaLife atende casos ELETIVOS.
- Use emojis com moderação: apenas 💙 ✅ 🩺 💳 👤 📱 📋 são permitidos.
- Responda sempre em português brasileiro formal.
- Seja objetivo(a). Evite respostas muito longas (máximo 3 parágrafos por mensagem).
- Se não souber responder algo, diga: "Vou verificar essa informação com nossa equipe
  e retornaremos em breve."
- O marcador ##TRIAGEM_CONCLUIDA## deve aparecer SOMENTE após o paciente confirmar o resumo.
  NUNCA inclua esse marcador antes da confirmação do paciente.
"""

EXTRATOR_PROMPT = """
Analise o histórico de conversa abaixo e extraia os dados de triagem do paciente.
Retorne APENAS um JSON válido, sem texto adicional, sem markdown, sem explicações.

Formato esperado:
{
  "nome": "...",
  "telefone": "...",
  "especialidade": "...",
  "convenio": "...",
  "descricao": "..."
}

Se algum campo não foi informado, use "Não informado".
"""


def _montar_historico(historico: list) -> list:
    """Converte histórico para o formato da nova SDK google-genai."""
    mensagens = []
    for msg in historico:
        role = "user" if msg["role"] == "user" else "model"
        mensagens.append(
            types.Content(role=role, parts=[types.Part(text=msg["content"])])
        )
    return mensagens


def obter_resposta_ia(historico: list) -> str:
    """Envia o histórico para o Gemini e retorna a resposta."""
    try:
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=500,
            temperature=0.5,
        )

        mensagens = _montar_historico(historico)

        resposta = client.models.generate_content(
            model=MODEL,
            contents=mensagens,
            config=config,
        )
        return resposta.text

    except Exception as e:
        print(f"⚠️ Erro na chamada ao Gemini: {e}")
        return (
            "Olá! No momento estamos com instabilidade técnica. "
            "Por favor, tente novamente em alguns instantes ou entre em contato pelo "
            "e-mail contato@optalife.com.br. Pedimos desculpas pelo inconveniente."
        )


def triagem_foi_concluida(resposta: str) -> bool:
    """Verifica se a resposta contém o marcador de triagem concluída."""
    return "##TRIAGEM_CONCLUIDA##" in resposta


def extrair_dados_triagem(historico: list) -> dict:
    """
    Extrai dados da triagem diretamente do resumo que a Olívia apresentou ao paciente.
    Busca o bloco de confirmação no histórico, muito mais confiável que pedir JSON à IA.
    """
    import re
    print(f"📋 [extrator] Histórico com {len(historico)} mensagens")

    dados = {
        "nome": "Não informado",
        "telefone": "Não informado",
        "especialidade": "Não informado",
        "convenio": "Não informado",
        "descricao": "Não informado"
    }

    # Busca a mensagem da Olívia que contém o resumo de confirmação
    resumo_texto = ""
    for msg in reversed(historico):
        if msg["role"] == "assistant" and "👤" in msg["content"] and "📱" in msg["content"]:
            resumo_texto = msg["content"]
            break

    if resumo_texto:
        print(f"📋 [extrator] Resumo encontrado: {resumo_texto[:200]}")

        def extrair_campo(texto, emoji, proximo_emoji=None):
            padrao = re.escape(emoji) + r"[\s\*]*[^:：]*[:：]\s*(.+)"
            match = re.search(padrao, texto)
            if match:
                valor = match.group(1).strip()
                # Remove asteriscos e texto após próximo emoji
                valor = valor.replace("*", "").strip()
                if proximo_emoji:
                    idx = valor.find(proximo_emoji)
                    if idx > 0:
                        valor = valor[:idx].strip()
                return valor
            return "Não informado"

        dados["nome"]          = extrair_campo(resumo_texto, "👤")
        dados["telefone"]      = extrair_campo(resumo_texto, "📱")
        dados["especialidade"] = extrair_campo(resumo_texto, "🩺")
        dados["convenio"]      = extrair_campo(resumo_texto, "💳")
        dados["descricao"]     = extrair_campo(resumo_texto, "📋")

        print(f"📋 [extrator] Dados extraídos: {dados}")
    else:
        print("📋 [extrator] Resumo não encontrado, usando fallback com IA...")
        try:
            historico_texto = "\n".join(
                f"{'Paciente' if m['role'] == 'user' else 'Olívia'}: {m['content']}"
                for m in historico
            )
            prompt = f"{EXTRATOR_PROMPT}\n\nHistórico:\n{historico_texto}"
            resposta = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.0, max_output_tokens=500),
            )
            texto = resposta.text.strip() if resposta.text else ""
            texto = texto.replace("```json", "").replace("```", "").strip()
            inicio = texto.find("{")
            fim = texto.rfind("}") + 1
            if inicio >= 0 and fim > inicio:
                texto = texto[inicio:fim]
                dados_ia = json.loads(texto)
                # Só atualiza campos que vieram preenchidos
                for campo in ("nome", "telefone", "especialidade", "convenio", "descricao"):
                    valor = dados_ia.get(campo, "").strip()
                    if valor and valor.lower() not in ("não informado", "nao informado", ""):
                        dados[campo] = valor
            else:
                print("⚠️ Fallback IA não retornou JSON válido — usando dados parciais do histórico")
                # Extrai o que der diretamente das mensagens do usuário
                msgs_usuario = [m["content"] for m in historico if m["role"] == "user"]
                if len(msgs_usuario) >= 1 and dados["nome"] == "Não informado":
                    dados["nome"] = msgs_usuario[0]
                if len(msgs_usuario) >= 2 and dados["telefone"] == "Não informado":
                    dados["telefone"] = msgs_usuario[1]
                if len(msgs_usuario) >= 3 and dados["especialidade"] == "Não informado":
                    dados["especialidade"] = msgs_usuario[2]
        except json.JSONDecodeError as e:
            print(f"⚠️ Erro ao parsear JSON do fallback: {e} — usando dados parciais do histórico")
            msgs_usuario = [m["content"] for m in historico if m["role"] == "user"]
            if len(msgs_usuario) >= 1 and dados["nome"] == "Não informado":
                dados["nome"] = msgs_usuario[0]
            if len(msgs_usuario) >= 2 and dados["telefone"] == "Não informado":
                dados["telefone"] = msgs_usuario[1]
            if len(msgs_usuario) >= 3 and dados["especialidade"] == "Não informado":
                dados["especialidade"] = msgs_usuario[2]
        except Exception as e:
            print(f"⚠️ Erro no fallback: {e}")

    return dados
