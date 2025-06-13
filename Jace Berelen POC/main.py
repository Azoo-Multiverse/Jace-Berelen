from fastapi import FastAPI, Request
from pydantic import BaseModel
import subprocess

app = FastAPI()

class SlackCommand(BaseModel):
    text: str
    user_name: str

@app.post("/slack/aider")
async def aider_command(payload: SlackCommand):
    # Simulate running aider with file
    result = subprocess.run(["echo", f"Running aider on: {payload.text}"], capture_output=True, text=True)
    return {"user": payload.user_name, "output": result.stdout.strip()}

@app.post("/slack/test")
async def test_command(payload: SlackCommand):
    result = subprocess.run(["pytest", payload.text], capture_output=True, text=True)
    return {"output": result.stdout.strip()}