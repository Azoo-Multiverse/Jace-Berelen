#!/usr/bin/env python3
"""
Quick Secret Generation for Railway Deploy
Generates secure keys needed for deployment
"""

import secrets
import string
from datetime import datetime

def generate_secret_key(length=32):
    """Generate a secure secret key"""
    return secrets.token_urlsafe(length)

def generate_railway_env():
    """Generate Railway environment variables template"""
    secret_key = generate_secret_key()
    
    env_template = f"""# ====================================================================
# JACE BERELEN POC - RAILWAY ENVIRONMENT VARIABLES
# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# ====================================================================

# SECURITY - GENERATED AUTOMATICALLY
SECRET_KEY={secret_key}

# SLACK CONFIGURATION - VOCÊ PRECISA PREENCHER ESTES
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token-here
SLACK_SIGNING_SECRET=your-slack-signing-secret-here
SLACK_APP_TOKEN=xapp-your-slack-app-token-here

# OPENROUTER AI - VOCÊ PRECISA PREENCHER ESTE
OPENROUTER_API_KEY=sk-or-your-openrouter-api-key-here

# RAILWAY CONFIGURATION - DEIXA ASSIM
ENVIRONMENT=production
DEBUG_MODE=false
LOG_LEVEL=INFO
RAILWAY_ENVIRONMENT=production
HOST=0.0.0.0

# AI MODEL CONFIGURATION - PODE PERSONALIZAR
AIDER_MODEL=anthropic/claude-3.5-sonnet
AI_MODEL_PRIMARY=anthropic/claude-3.5-sonnet
AI_MODEL_FALLBACK=anthropic/claude-3-haiku
OPENROUTER_SITE_URL=https://jace-berelen.railway.app
OPENROUTER_APP_NAME=Jace Berelen POC

# COST MANAGEMENT - AJUSTA CONFORME NECESSÁRIO
MONTHLY_BUDGET_LIMIT=100.0
AI_COST_ALERT_THRESHOLD=80.0
DEFAULT_CLIENT_BUDGET=20.0

# SECURITY & RATE LIMITING
RATE_LIMIT_PER_MINUTE=60
SESSION_TIMEOUT_MINUTES=30

# FEATURE FLAGS
ENABLE_WEB_SCRAPING=true
ENABLE_FILE_UPLOADS=false
ENABLE_SYSTEM_COMMANDS=false
"""
    
    return env_template

def main():
    """Main function"""
    print("🔐 Generating Railway deployment secrets...")
    print("="*60)
    
    # Generate new secret key
    secret_key = generate_secret_key()
    print(f"✅ Generated SECRET_KEY: {secret_key}")
    
    # Generate full env template
    env_content = generate_railway_env()
    
    # Save to file
    with open("railway-env-generated.txt", "w") as f:
        f.write(env_content)
    
    print("✅ Saved complete environment template to: railway-env-generated.txt")
    print()
    print("🚀 PRÓXIMOS PASSOS:")
    print("1. Abra o arquivo railway-env-generated.txt")
    print("2. Preencha seus tokens do Slack e OpenRouter")
    print("3. Copie todas as variáveis para o Railway dashboard")
    print("4. Deploy! 🎉")
    print()
    print("📋 VOCÊ PRECISA CONFIGURAR:")
    print("- SLACK_BOT_TOKEN (vai em https://api.slack.com/apps)")
    print("- SLACK_SIGNING_SECRET (mesma página)")
    print("- OPENROUTER_API_KEY (vai em https://openrouter.ai)")
    print()
    print("💡 DICA: O SECRET_KEY já foi gerado automaticamente!")

if __name__ == "__main__":
    main() 