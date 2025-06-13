# Jace Berelen - Stage 0 POC

This is the minimal setup to test Jace locally with:

- A FastAPI app to respond to Slack commands
- Routes to simulate Aider and Pytest automation
- .env file to load secrets (tokens and keys)

## Usage

1. Set up your `.env` file based on `.env.example`
2. Run locally with:

```bash
uvicorn main:app --reload
```

3. Use Slack to POST commands to `/slack/aider` or `/slack/test`

4. Extend with Trello and Supabase integration later.