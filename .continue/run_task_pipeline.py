import os
import requests
import shutil
import subprocess
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    raise Exception("API Key not found.")

API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "anthropic/claude-sonnet-4"

TODO_FOLDER = "TASKS\\TODO"
DONE_FOLDER = "TASKS\\DONE"

def execute_task(prompt):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0,
        "max_tokens": 4096
    }

    response = requests.post(API_URL, headers=headers, json=data)
    if response.status_code != 200:
        print(f"Request error {response.status_code}: {response.text}")
        return None

    result = response.json()
    return result['choices'][0]['message']['content']

def process_task(task_folder):
    task_name = os.path.basename(task_folder)
    task_md = os.path.join(task_folder, f"{task_name}.md")

    if not os.path.isfile(task_md):
        print(f"Task file {task_md} not found. Skipping.")
        return

    with open(task_md, "r", encoding="utf-8") as f:
        prompt = f.read().strip()

    print(f"Running task: {task_name}")
    output = execute_task(prompt)

    if output:
        report_path = os.path.join(task_folder, f"report_{task_name}.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(output)

    done_path = os.path.join(DONE_FOLDER, task_name)
    shutil.move(task_folder, done_path)

    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", f"Task {task_name} completed"], check=True)

def main():
    os.makedirs(DONE_FOLDER, exist_ok=True)

    tasks = [
        os.path.join(TODO_FOLDER, d)
        for d in os.listdir(TODO_FOLDER)
        if os.path.isdir(os.path.join(TODO_FOLDER, d))
    ]

    if not tasks:
        print("No tasks found in TODO.")
        return

    for task in tasks:
        process_task(task)

if __name__ == "__main__":
    main()
