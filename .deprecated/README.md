# Jace Berelen POC 🤖

AI-driven workflow automation platform for overemployment support.

## 🚀 Quick Start (Local Development)

1. **Install ngrok** (for public URLs):
   ```bash
   # Windows (Chocolatey)
   choco install ngrok
   
   # Mac (Homebrew)
   brew install ngrok
   
   # Or download from: https://ngrok.com/download
   ```

2. **Run the automated starter**:
   ```bash
   python start-local.py
   ```

That's it! The script will:
- ✅ Start ngrok tunnel automatically
- ✅ Generate secure `.env` file with ngrok URL
- ✅ Show Slack configuration instructions
- ✅ Start the application when ready

## 📁 Configuration Architecture

This project uses a **dual configuration system**:

### 📋 `env.py` - Public Configurations
- ✅ **Safe to commit to git**
- Contains defaults, model configs, endpoints, validation rules
- No sensitive information

### 🔐 `.env` - Secrets Only
- ❌ **NEVER commit to git** (protected by .gitignore)
- Contains API keys, tokens, passwords only
- Generated automatically by `start-local.py`

### 🔧 How It Works

```python
# env.py (public)
DEFAULT_AI_MODEL = "anthropic/claude-3.5-sonnet"
DEFAULT_PORT = 8000

# .env (secrets)
OPENROUTER_API_KEY=sk-or-your-key-here
SLACK_BOT_TOKEN=xoxb-your-token-here

# src/config.py (combines both)
from env import *  # Import public configs
class Settings(BaseSettings):  # Load secrets from .env
    ai_model: str = Field(default=DEFAULT_AI_MODEL)
    openrouter_api_key: str = Field(alias="OPENROUTER_API_KEY")
```

## 🛠️ Manual Setup

If you prefer manual configuration:

1. **Clone and install dependencies**:
   ```bash
   git clone <repository>
   cd "Jace Berelen POC"
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   pip install -r requirements.txt
   ```

2. **Create environment file**:
   ```bash
   cp env-template.txt .env
   ```

3. **Edit `.env` with your credentials**:
   - Get Slack tokens from https://api.slack.com/apps
   - Get OpenRouter API key from https://openrouter.ai
   - Fill in the placeholder values

4. **Start application**:
   ```bash
   python run.py
   ```

## 🌐 Configuration Details

### Required Secrets (`.env`)
- `SECRET_KEY` - App security (auto-generated)
- `SLACK_BOT_TOKEN` - Bot token from Slack app
- `SLACK_SIGNING_SECRET` - Signing secret from Slack app
- `OPENROUTER_API_KEY` - OpenRouter API key for AI models

### Optional Overrides (`.env`)
- `ENVIRONMENT` - development/production/staging
- `DEBUG_MODE` - true/false
- `LOG_LEVEL` - DEBUG/INFO/WARNING/ERROR
- `PUBLIC_URL` - For development tunneling
- `DATABASE_URL` - Custom database (defaults to SQLite)

## 📱 Slack App Configuration

When using `start-local.py`, you'll get automatic instructions for:

1. **Event Subscriptions URL**: `https://your-ngrok-url.com/webhooks/slack`
2. **OAuth Redirect URL**: `https://your-ngrok-url.com/slack/oauth`
3. **Required Scopes**: Bot permissions for your workspace

## 🔧 API Endpoints

- **Health Check**: `/health`
- **API Documentation**: `/docs`
- **AI Chat**: `/ai/chat`
- **Task Management**: `/tasks`
- **Slack Webhooks**: `/webhooks/slack`
- **Usage Metrics**: `/metrics/usage`

## 🚀 Railway Deployment

For production deployment:

1. Create Railway project
2. Set environment variables in Railway dashboard:
   ```
   SECRET_KEY=<generate-strong-key>
   SLACK_BOT_TOKEN=xoxb-...
   SLACK_SIGNING_SECRET=...
   OPENROUTER_API_KEY=sk-or-...
   ENVIRONMENT=production
   ```
3. Deploy automatically via git push

## 🔒 Security Features

- ✅ Automatic secret generation
- ✅ Token format validation  
- ✅ Environment-based CORS restrictions
- ✅ Rate limiting
- ✅ Cost monitoring with alerts
- ✅ Secrets never committed to git

## 🤖 AI Models Supported

- **Primary**: Claude 3.5 Sonnet (high quality)
- **Fallback**: Claude 3 Haiku (fast/cheap)
- **Custom**: Configure any OpenRouter model

## 📊 Cost Management

- Monthly budget limits
- Real-time cost tracking
- Alert thresholds
- Per-client budget controls

## 🏗️ Architecture

```
├── env.py              # Public configurations (committed)
├── .env               # Secrets only (never committed)
├── src/
│   ├── config.py      # Configuration management
│   ├── database.py    # Database models
│   ├── ai_client.py   # OpenRouter/Claude integration
│   └── logger.py      # Logging setup
├── start-local.py     # Automated local development
└── run.py            # Application entry point
```

## 🆘 Troubleshooting

### ngrok Issues
- Ensure ngrok is installed and in PATH
- Check firewall settings for port 4040
- Restart script if tunnel fails

### Slack Integration
- Verify bot tokens are correct format (`xoxb-`)
- Check signing secret matches Slack app
- Ensure webhook URLs are updated in Slack app

### AI Integration
- Verify OpenRouter API key format (`sk-or-`)  
- Check model availability and quotas
- Monitor cost alerts

## 🤝 Contributing

1. Public configs go in `env.py`
2. Secrets go in `.env` (never commit!)
3. Use `start-local.py` for development
4. Test with real Slack workspace

---

**Jace Berelen POC** - Making overemployment workflows effortless! 🚀 