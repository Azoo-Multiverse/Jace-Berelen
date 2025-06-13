# Jace Berelen POC

**AI-Driven Workflow Automation Platform for Overemployment Support**

> Manage multiple jobs simultaneously with AI-powered task automation, secure command execution, and intelligent workflow coordination.

![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Setup Guide](#setup-guide)
- [Usage](#usage)
- [Command Execution](#command-execution)
- [API Documentation](#api-documentation)
- [Security](#security)
- [Architecture](#architecture)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## Overview

Jace Berelen POC is an AI-powered assistant designed specifically for overemployed professionals who need to manage multiple jobs efficiently. It provides:

- **AI-powered task management** via Claude 3.5 Sonnet (through OpenRouter)
- **Slack integration** for seamless workflow management
- **Secure command execution** (AWS CLI, Git, npm, etc.) within isolated workspaces
- **Multi-job coordination** and prioritization
- **Cost tracking** and budget management
- **Automated task breakdown** and execution planning

### Perfect For:
- Managing 3-5 remote jobs simultaneously
- Automating repetitive development tasks
- Coordinating deadlines across multiple clients
- Secure execution of CLI commands per project
- AI-assisted communication and planning

---

## Features

### **AI-Powered Assistance**
- **Claude 3.5 Sonnet** integration via OpenRouter
- Natural language task breakdown
- Code generation and debugging
- Professional communication templates
- Intelligent prioritization across jobs

### **Slack Integration**
- **Slash Commands**: `/jace`, `/tasks`, `/ai`
- **Direct Messages**: Natural conversation with AI
- **Real-time notifications** and status updates
- **Interactive task management** with buttons and forms

### **Secure Command Execution**
- **Workspace Isolation**: Each task gets its own secure folder
- **Whitelisted Commands**: AWS CLI, Git, npm, Docker, Terraform
- **Security Blocking**: Prevents dangerous operations
- **Audit Logging**: All commands tracked and logged

### **Multi-Job Management**
- **Task Prioritization** across multiple employers
- **Time Tracking** and productivity metrics
- **Budget Management** with AI cost monitoring
- **Deadline Coordination** and conflict resolution

### **Enterprise Security**
- Environment-based configuration
- API key rotation support
- Comprehensive audit trails
- Isolated execution environments

---

## Quick Start

### Prerequisites
- Python 3.11+
- OpenRouter API key ([get one here](https://openrouter.ai))
- Slack App with bot token ([create one here](https://api.slack.com/apps))

### 1-Minute Setup
```bash
# Clone and navigate
git clone <repository-url>
cd "Jace Berelen POC"

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp environment.txt .env
# Edit .env with your API keys

# Test setup
python test_setup.py

# Run the application
python run.py
```

**That's it!** Your AI assistant is now running at `http://localhost:8000`

---

## Setup Guide

### Step 1: Environment Configuration

Create your `.env` file:
```bash
cp environment.txt .env
```

Edit `.env` with your actual credentials:
```env
# Required - Get from OpenRouter
OPENROUTER_API_KEY=sk-or-your-openrouter-key-here

# Required - Get from Slack App
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token-here
SLACK_SIGNING_SECRET=your-32-character-signing-secret

# Required - Generate a secure random string
SECRET_KEY=your-super-secret-key-here

# Optional - OpenRouter app info
OPENROUTER_SITE_URL=https://your-company.com
OPENROUTER_APP_NAME=Your Company Bot
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Verify Setup
```bash
python test_setup.py
```

This will check:
- All imports working
- Environment variables set
- OpenRouter API connection
- Database initialization
- Command executor setup

### Step 4: Run Application
```bash
python run.py
```

### Step 5: Configure Slack App

1. **Create Slack App** at [api.slack.com/apps](https://api.slack.com/apps)

2. **Add Bot Scopes** (OAuth & Permissions):
   ```
   app_mentions:read
   channels:read
   chat:write
   commands
   files:write
   im:read
   im:write
   users:read
   ```

3. **Create Slash Commands**:
   - `/jace` → `http://your-domain.com/webhooks/slack`
   - `/tasks` → `http://your-domain.com/webhooks/slack`
   - `/ai` → `http://your-domain.com/webhooks/slack`

4. **Install App** to your workspace

---

## Usage

### Slack Commands

#### `/jace` - Main AI Assistant
```bash
/jace help                    # Show help information
/jace create Review PR #123   # Create a new task
/jace status                  # Show current status
/jace tasks                   # List active tasks
```

#### `/tasks` - Task Management
```bash
/tasks                        # List all active tasks
/tasks create Deploy staging  # Create task
/tasks complete 5             # Mark task #5 complete
```

#### `/ai` - Direct AI Interaction
```bash
/ai How do I prioritize 3 conflicting deadlines?
/ai Generate a Python function to parse CSV files
/ai Draft an email explaining a project delay
```

### Direct Messages

Simply message the bot directly for natural conversation:
```
Hi Jace, I need help managing my workload across 4 different projects

Create task: Review pull requests for Project Alpha

What's the best way to automate deployment for my Node.js app?
```

### API Endpoints

#### Chat with AI
```bash
POST http://localhost:8000/ai/chat
{
  "prompt": "Help me break down this complex task",
  "system_prompt": "You are an expert project manager",
  "temperature": 0.1
}
```

#### Task Management
```bash
GET  http://localhost:8000/tasks        # List tasks
POST http://localhost:8000/tasks        # Create task
{
  "title": "Deploy to staging",
  "description": "Deploy latest code to staging environment",
  "priority": "high"
}
```

#### Health Check
```bash
GET http://localhost:8000/health
```

---

## Command Execution

Jace can securely execute commands within isolated task workspaces.

### Supported Commands

#### AWS CLI
```bash
/jace run aws s3 ls
/jace run aws ec2 describe-instances --region us-west-2
/jace run aws lambda list-functions
/jace run aws sts get-caller-identity
```

#### Git Operations
```bash
/jace run git status
/jace run git add .
/jace run git commit -m "Update documentation"
/jace run git push origin main
/jace run git pull origin develop
```

#### Node.js Development
```bash
/jace run npm install
/jace run npm run build
/jace run npm test
/jace run npx create-react-app my-app
```

#### Python Development
```bash
/jace run python app.py
/jace run pip install requests
/jace run python -m pytest tests/
```

#### Docker Operations
```bash
/jace run docker ps
/jace run docker images
/jace run docker logs container-name
/jace run docker build -t my-app .
```

#### Infrastructure as Code
```bash
/jace run terraform init
/jace run terraform plan
/jace run terraform apply
/jace run kubectl get pods
```

### Security Features

- **Workspace Isolation**: Each task runs in `workspaces/user_{id}_task_{id}/`
- **Command Whitelist**: Only approved commands allowed
- **Dangerous Command Blocking**: Prevents `rm -rf`, `sudo`, etc.
- **Path Validation**: No directory traversal allowed
- **Timeout Protection**: Commands auto-killed after 30 seconds
- **Audit Logging**: All commands logged with user/task context

---

## API Documentation

### Interactive Documentation
Visit `http://localhost:8000/docs` for full interactive API documentation.

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Application info |
| `/health` | GET | Health check |
| `/ai/chat` | POST | Chat with AI |
| `/ai/code-help` | POST | Code assistance |
| `/ai/task-breakdown` | POST | Break down tasks |
| `/tasks` | GET/POST | Task management |
| `/metrics/usage` | GET | AI usage metrics |
| `/webhooks/slack` | POST | Slack events |

### Response Examples

#### AI Chat Response
```json
{
  "content": "Here's how to prioritize your tasks...",
  "model_used": "anthropic/claude-3.5-sonnet",
  "tokens_used": 150,
  "cost_usd": 0.0045,
  "response_time_ms": 1200
}
```

#### Task List Response
```json
{
  "tasks": [
    {
      "id": 1,
      "title": "Review pull request #123",
      "status": "pending",
      "priority": "high",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1
}
```

---

## Security

### Data Protection
- **Environment Variables**: All secrets in `.env` (never committed)
- **API Key Rotation**: Easy key rotation without code changes
- **Workspace Isolation**: Commands can't access other task data
- **Audit Trails**: All actions logged with timestamps

### Command Security
- **Whitelist-Only**: Only approved commands can run
- **Blocked Patterns**: Dangerous operations automatically blocked
- **Path Restrictions**: No access outside task workspace
- **Timeout Limits**: Runaway commands auto-terminated

### Network Security
- **HTTPS Ready**: SSL/TLS configuration included
- **CORS Protection**: Configurable cross-origin policies
- **Rate Limiting**: Prevent API abuse
- **Input Validation**: All inputs sanitized

---

## Architecture

### Core Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Slack Bot     │────│   FastAPI App   │────│  OpenRouter AI  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────│   Database      │──────────────┘
                        │   (SQLite)      │
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │ Command Executor │
                        │  (Isolated)     │
                        └─────────────────┘
```

### Technology Stack

- **Backend**: FastAPI + Python 3.11+
- **AI**: Claude 3.5 Sonnet via OpenRouter
- **Database**: SQLite (Stage 0) → PostgreSQL (Production)
- **Communication**: Slack SDK
- **Security**: Pydantic validation + workspace isolation
- **Deployment**: Docker ready, Railway/AWS compatible

### File Structure

```
Jace Berelen POC/
├── src/                     # Core application code
│   ├── config.py           # Configuration management
│   ├── ai_client.py        # OpenRouter AI integration
│   ├── slack_handler.py    # Slack bot implementation
│   ├── database.py         # Data models and operations
│   ├── command_executor.py # Secure command execution
│   ├── agents.py           # Specialized AI agents
│   ├── utils.py            # Utility functions
│   └── main.py             # FastAPI application
├── workspaces/             # Isolated task execution folders
├── logs/                   # Application logs
├── requirements.txt        # Python dependencies
├── environment.txt         # Environment template
├── run.py                  # Application launcher
└── test_setup.py          # Setup verification
```

---

## Troubleshooting

### Common Issues

#### "Environment validation failed"
```bash
# Check your .env file exists and has required variables
cat .env
python test_setup.py
```

#### "OpenRouter API key invalid"
```bash
# Verify your key starts with 'sk-or-'
echo $OPENROUTER_API_KEY
# Test the key at openrouter.ai
```

#### "Slack bot not responding"
```bash
# Check bot token starts with 'xoxb-'
# Verify signing secret is 32 characters
# Ensure bot has proper scopes in Slack app settings
```

#### "Command execution failed"
```bash
# Check if command is in whitelist
python -c "from src import command_executor; print(command_executor.get_allowed_commands())"

# Verify workspace permissions
ls -la workspaces/
```

### Debug Mode

Enable debug logging:
```env
LOG_LEVEL=DEBUG
DEBUG_MODE=true
```

### Health Checks

```bash
# Application health
curl http://localhost:8000/health

# Database connectivity
python -c "from src import db_manager; print(db_manager.health_check())"

# AI client test
python -c "from src import ai_client; print('AI client ready')"
```

### Log Files

Check logs for detailed error information:
```bash
tail -f logs/jace_$(date +%Y%m%d).log
```

---

## Next Steps & Roadmap

### Stage 0 (Current) - MVP
- Basic AI assistant functionality
- Slack integration
- Secure command execution
- Task management
- OpenRouter integration

### Stage 1 - Enhanced Features
- [ ] Multi-user support with authentication
- [ ] PostgreSQL database migration
- [ ] Redis caching for performance
- [ ] Enhanced workflow automation
- [ ] GitHub/GitLab integration

### Stage 2 - Production Ready
- [ ] Kubernetes deployment
- [ ] Advanced monitoring and alerting
- [ ] Multi-tenant architecture
- [ ] Advanced AI agents
- [ ] Mobile application

### Stage 3 - SaaS Platform
- [ ] Public API with rate limiting
- [ ] Subscription billing
- [ ] Advanced analytics dashboard
- [ ] Custom AI model training
- [ ] Enterprise integrations

---

## Tips & Best Practices

### Optimal Usage Patterns

1. **Start Small**: Begin with 2-3 jobs, gradually increase
2. **Task Naming**: Use clear, actionable task names
3. **Workspace Organization**: Keep task-specific files organized
4. **Regular Cleanup**: Archive completed tasks periodically
5. **Cost Monitoring**: Check `/metrics/usage` regularly

### Command Best Practices

```bash
# Good: Specific, safe commands
/jace run aws s3 ls s3://my-bucket/
/jace run git status

# Avoid: Broad, potentially dangerous commands
/jace run rm -rf *
/jace run sudo anything
```

### AI Prompt Engineering

```bash
# Specific, context-rich prompts
/ai I have 3 Node.js projects due this week. Project A needs testing, Project B needs deployment, Project C needs code review. How should I prioritize?

# Vague prompts
/ai Help me with work
```

---

## Support & Contributing

### Getting Help

1. **Check the logs**: `logs/jace_YYYYMMDD.log`
2. **Run diagnostics**: `python test_setup.py`
3. **Review documentation**: `/docs` endpoint
4. **Check GitHub Issues**: [Project Issues](link-to-issues)

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Code formatting
black src/
isort src/

# Type checking
mypy src/
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **OpenRouter** for providing unified AI model access
- **Anthropic** for the Claude AI models
- **Slack** for the excellent platform and APIs
- **FastAPI** for the fantastic web framework
- **Python Community** for the amazing ecosystem

---

**Jace Berelen POC - Making overemployment manageable, one task at a time.**

*Built with love for the overemployed community* 