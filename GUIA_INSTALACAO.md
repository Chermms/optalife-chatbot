# 🤖 CHATBOT OPTALIFE — GUIA DE INSTALAÇÃO COMPLETO

Bem-vindo ao guia de configuração do Chatbot da OptaLife!
Siga cada etapa com calma. Tempo estimado: **30 a 45 minutos**.

---

## 📁 ESTRUTURA DOS ARQUIVOS

```
optalife_chatbot/
├── app.py              → Servidor principal (recebe mensagens do WhatsApp)
├── groq_client.py      → Inteligência Artificial (Groq) + Script de atendimento
├── memoria.py          → Memória das conversas
├── requirements.txt    → Bibliotecas necessárias
├── render.yaml         → Configuração de deploy (Render.com)
├── .env.example        → Modelo das variáveis de ambiente
└── GUIA_INSTALACAO.md  → Este guia
```

---

## ETAPA 1 — Criar conta no Groq (IA gratuita)

1. Acesse: **https://console.groq.com**
2. Clique em **"Sign Up"** e crie uma conta gratuita
3. Após login, clique em **"API Keys"** no menu lateral
4. Clique em **"Create API Key"**
5. Copie a chave gerada (começa com `gsk_...`)
6. Guarde essa chave — você usará na Etapa 4

---

## ETAPA 2 — Criar conta de desenvolvedor na Meta (WhatsApp)

1. Acesse: **https://developers.facebook.com**
2. Faça login com sua conta do Facebook
3. Clique em **"Meus Apps"** > **"Criar App"**
4. Escolha o tipo: **"Empresa"**
5. Dê um nome ao app: ex. `OptaLife Chatbot`
6. Na tela do app, clique em **"Configurar"** dentro do card **WhatsApp**
7. Siga o assistente e adicione um número de telefone de teste

> 💡 **Dica:** Para usar um número real (não de teste), você precisará de uma
> conta do WhatsApp Business verificada. Para começar, o número de teste já funciona.

8. Anote os valores na tela **"Configurações da API"**:
   - **Token de acesso temporário** → será o `WHATSAPP_TOKEN`
   - **ID do número de telefone** → será o `PHONE_NUMBER_ID`

---

## ETAPA 3 — Fazer o deploy no Render.com (hospedagem gratuita)

1. Acesse: **https://render.com** e crie uma conta gratuita
2. Clique em **"New"** > **"Web Service"**
3. Conecte ao **GitHub** (você precisará criar uma conta gratuita se não tiver)
4. Crie um repositório no GitHub e faça upload dos arquivos do projeto
   - Acesse **https://github.com** > **"New repository"**
   - Nomeie: `optalife-chatbot`
   - Faça upload de todos os arquivos desta pasta
5. No Render, selecione o repositório `optalife-chatbot`
6. Configure:
   - **Name:** `optalife-chatbot`
   - **Region:** `Oregon (US West)` ou qualquer um
   - **Branch:** `main`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
7. Clique em **"Create Web Service"**
8. Aguarde o deploy. Quando aparecer **"Live"**, copie a URL gerada
   - Exemplo: `https://optalife-chatbot.onrender.com`

---

## ETAPA 4 — Configurar as variáveis de ambiente no Render

1. No painel do Render, acesse seu serviço > **"Environment"**
2. Clique em **"Add Environment Variable"** e adicione as 4 variáveis:

| Chave            | Valor                                  |
|------------------|----------------------------------------|
| GROQ_API_KEY     | A chave da Etapa 1 (começa com gsk_...) |
| WHATSAPP_TOKEN   | Token copiado na Etapa 2               |
| PHONE_NUMBER_ID  | ID do número copiado na Etapa 2        |
| VERIFY_TOKEN     | Digite qualquer palavra. Ex: optalife2026 |

3. Clique em **"Save Changes"** — o serviço reiniciará automaticamente

---

## ETAPA 5 — Configurar o Webhook no Meta for Developers

1. Volte para **https://developers.facebook.com** > seu app
2. No menu esquerdo, clique em **WhatsApp** > **Configuração**
3. Na seção **"Webhooks"**, clique em **"Editar"**
4. Preencha:
   - **URL do Callback:** `https://optalife-chatbot.onrender.com/webhook`
     *(substitua pela sua URL real do Render)*
   - **Token de Verificação:** `optalife2026`
     *(o mesmo valor que você digitou em VERIFY_TOKEN)*
5. Clique em **"Verificar e Salvar"**
6. Se aparecer ✅ verde, funcionou!
7. Em **"Campos do Webhook"**, ative: **messages**

---

## ETAPA 6 — Testar o chatbot

1. No painel Meta, vá em **WhatsApp** > **Configurações da API**
2. No campo **"Para"**, insira seu número pessoal
3. Envie uma mensagem de teste pelo seu WhatsApp para o número de teste da OptaLife
4. O chatbot deverá responder automaticamente em segundos!

---

## ⚠️ PROBLEMAS COMUNS

**O webhook não verificou:**
→ Confirme que a URL do Render está correta e o serviço está "Live"
→ Confirme que o VERIFY_TOKEN é idêntico nos dois lugares

**O chatbot não responde:**
→ Verifique os logs em Render > seu serviço > "Logs"
→ Confirme que o WHATSAPP_TOKEN ainda é válido (tokens temporários expiram)

**Erro de token expirado:**
→ Tokens temporários da Meta duram ~24h. Para uso contínuo, gere um
  "Token de Acesso de Sistema" permanente no Gerenciador de Negócios da Meta.

---

## 📞 PERSONALIZAR O SCRIPT DE ATENDIMENTO

Para alterar as respostas do chatbot, edite o arquivo **`groq_client.py`**,
especificamente o texto dentro da variável `SYSTEM_PROMPT`.

Após editar, faça o commit no GitHub — o Render atualizará automaticamente.

---

## 🆓 LIMITES DO PLANO GRATUITO

| Serviço  | Limite gratuito                              |
|----------|----------------------------------------------|
| Groq     | ~14.400 requisições/dia (mais que suficiente) |
| Render   | Servidor "dorme" após 15min de inatividade   |
| Meta API | Ilimitado para números verificados           |

> 💡 O "sono" do Render significa que a primeira mensagem após inatividade
> pode demorar ~30 segundos. Após isso, funciona normalmente.

---

*OptaLife Chatbot — Versão 1.0 | 2026*
