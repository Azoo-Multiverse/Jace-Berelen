# 🚀 Railway Deployment Guide - Jace Berelen POC

Este guia te leva do zero ao deploy em **menos de 10 minutos**!

## ⚡ Quick Start (Método mais rápido)

### 1. Fazer Deploy no Railway

1. **Fork este repositório** no seu GitHub
2. **Vai no [Railway](https://railway.app)** e faz login com GitHub
3. **Clica em "New Project"** → "Deploy from GitHub repo"
4. **Seleciona seu fork** do Jace Berelen POC
5. **Boom!** Railway vai detectar automaticamente e começar o build

### 2. Adicionar PostgreSQL

1. No seu projeto Railway, clica **"+ New Service"**
2. Seleciona **"Database" → "PostgreSQL"**
3. Railway vai criar automaticamente a `DATABASE_URL`

### 3. Configurar Variáveis de Ambiente

No Railway dashboard, vai em **"Variables"** e adiciona:

```bash
# OBRIGATÓRIAS - SEM ESSAS NÃO FUNCIONA!
SECRET_KEY=sua-super-secret-key-muito-forte-aqui-mude-isso
SLACK_BOT_TOKEN=xoxb-seu-token-do-slack-bot
SLACK_SIGNING_SECRET=seu-signing-secret-do-slack
OPENROUTER_API_KEY=sk-or-sua-api-key-do-openrouter

# OPCIONAIS - JÁ TEM VALORES PADRÃO
ENVIRONMENT=production
DEBUG_MODE=false
LOG_LEVEL=INFO
RAILWAY_ENVIRONMENT=production
```

### 4. Deploy Automático

Railway vai fazer **deploy automático** a cada push! 🎉

---

## 📋 Configuração Detalhada

### Slack Bot Setup

1. **Vai no [Slack API](https://api.slack.com/apps)**
2. **Cria uma nova app** ou usa uma existente
3. **Pega as credenciais:**
   - `SLACK_BOT_TOKEN`: Em "OAuth & Permissions" (começa com `xoxb-`)
   - `SLACK_SIGNING_SECRET`: Em "Basic Information" → "App Credentials"

### OpenRouter API Setup

1. **Vai no [OpenRouter](https://openrouter.ai)**
2. **Cria conta e pega API key** (começa com `sk-or-`)
3. **Coloca no Railway:** `OPENROUTER_API_KEY=sk-or-sua-key`

### Secret Key Geração

**Gera uma secret key forte:**

```bash
# Opção 1: Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Opção 2: OpenSSL
openssl rand -base64 32
```

---

## 🔧 Arquivos de Configuração

### `railway.toml`
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "python run.py"
healthcheckPath = "/health"
```

### `Procfile`
```
web: python run.py
worker: python -m src.agents
```

---

## ✅ Verificação do Deploy

Após o deploy, testa estes endpoints:

1. **Health Check:** `https://seu-app.railway.app/health`
2. **API Docs:** `https://seu-app.railway.app/docs`
3. **Root:** `https://seu-app.railway.app/`

**Resposta esperada do `/health`:**
```json
{
  "status": "healthy",
  "environment": "production",
  "database_connected": true,
  "ai_connected": true
}
```

---

## 🚨 Troubleshooting

### Deploy Falhando?

**1. Verifica as variáveis obrigatórias:**
```bash
SECRET_KEY         ✅ Definida?
SLACK_BOT_TOKEN    ✅ Começa com xoxb-?
SLACK_SIGNING_SECRET ✅ Definida?
OPENROUTER_API_KEY   ✅ Começa com sk-or-?
```

**2. Verifica os logs:**
- Railway Dashboard → Seu projeto → "Deployments" → "View Logs"

**3. Testa localmente primeiro:**
```bash
# Copia as envs do railway-env.txt
# Roda local para testar
python run.py
```

### Database Issues?

**Railway PostgreSQL não conectando?**
- Verifica se o serviço PostgreSQL está rodando
- `DATABASE_URL` é setada automaticamente pelo Railway
- Logs devem mostrar "Database initialized successfully"

### AI não funcionando?

**OpenRouter API issues?**
```bash
# Testa a API key
curl -H "Authorization: Bearer sk-or-sua-key" \
     https://openrouter.ai/api/v1/models
```

---

## 📊 Monitoramento

### Logs em Tempo Real
```bash
# Railway CLI (opcional)
railway logs --follow
```

### Métricas Importantes
- **Health endpoint:** Sempre monitora `/health`
- **Database:** Conexões PostgreSQL
- **AI Usage:** Custos OpenRouter
- **Response time:** < 2s para endpoints principais

---

## 💰 Custos

### Railway
- **Hobby Plan:** $5/mês (suficiente para POC)
- **PostgreSQL:** Incluso no plano

### OpenRouter
- **Claude 3.5 Sonnet:** ~$3-15/milhão tokens
- **Budget recomendado:** $20-50/mês para testes

---

## 🔄 Atualizações

**Deploy automático:** Push para main branch → Deploy automático!

```bash
git add .
git commit -m "feat: nova feature incrível"
git push origin main
# Railway faz deploy automático! 🚀
```

---

## 🎯 Próximos Passos

Após deploy bem-sucedido:

1. **Testa todos os endpoints**
2. **Configura Slack webhook** apontando para seu Railway URL
3. **Monitora custos** OpenRouter
4. **Escala conforme necessário**

**URL final:** `https://jace-berelen-poc.railway.app`

---

## 📞 Suporte

**Problemas?** Verifica:
1. **Logs do Railway** primeiro
2. **Variáveis de ambiente** estão corretas
3. **Health endpoint** está respondendo
4. **Database** conectado

**Dica:** Railway tem **deploy super rápido**, então faz quantos testes precisar! 🔥 