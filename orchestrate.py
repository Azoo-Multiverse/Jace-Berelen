import os
import json
import time
from pathlib import Path
from typing import Dict, List
from datetime import datetime

class TaskOrchestrator:
    def __init__(self):
        self.root_dir = Path(os.getcwd())
        self.todo_dir = self.root_dir / "TASKS" / "TODO"
        self.done_dir = self.root_dir / "TASKS" / "DONE"
        self.in_progress_dir = self.root_dir / "TASKS" / "IN_PROGRESS"
        self.agents_dir = self.root_dir / "TASKS" / "AGENTS"
        
        # Create necessary directories
        for dir_path in [self.todo_dir, self.done_dir, self.in_progress_dir, self.agents_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def create_agent_tasks(self, task_id: str) -> None:
        """Creates subtasks for each agent based on main task"""
        agents = ["strategist", "developer", "reviewer", "validator"]
        
        for agent in agents:
            task_file = self.agents_dir / f"{agent}_template.md"
            if task_file.exists():
                template = task_file.read_text()
                new_task = template.replace("${task_id}", task_id)
                new_task = new_task.replace("${timestamp}", datetime.now().isoformat())
                
                agent_task_file = self.todo_dir / f"{task_id}_{agent}.md"
                agent_task_file.write_text(new_task)

    def get_next_task(self) -> Dict:
        """Gets the next task to be processed based on dependencies"""
        tasks = list(self.todo_dir.glob("*.md"))
        if not tasks:
            return None
            
        # Read task metadata and check dependencies
        for task_path in tasks:
            with open(task_path, 'r') as f:
                content = f.read()
                if "dependencies:" in content:
                    deps = [d.strip() for d in content.split("dependencies:")[1].split("\n")[0].split(",")]
                    if all(self.is_task_completed(d) for d in deps):
                        return {"path": task_path, "content": content}
                else:
                    return {"path": task_path, "content": content}
        
        return None

    def is_task_completed(self, task_id: str) -> bool:
        """Checks if a task is completed"""
        return any((self.done_dir / f"{task_id}*").glob("*"))

    def move_to_in_progress(self, task_path: Path) -> None:
        """Moves task to IN_PROGRESS folder"""
        dest = self.in_progress_dir / task_path.name
        task_path.rename(dest)

    def move_to_done(self, task_id: str) -> None:
        """Moves completed task to DONE folder"""
        for task_file in self.in_progress_dir.glob(f"{task_id}*"):
            dest = self.done_dir / task_file.name
            task_file.rename(dest)

    def run(self) -> None:
        """Main orchestration loop"""
        print("Starting task orchestration...")
        
        while True:
            next_task = self.get_next_task()
            if not next_task:
                print("No tasks available. Waiting...")
                time.sleep(10)
                continue

            task_path = next_task["path"]
            print(f"Processing task: {task_path.name}")
            
            # Move to in progress
            self.move_to_in_progress(task_path)
            
            # Create agent subtasks if this is a main task
            if "type: main" in next_task["content"]:
                task_id = task_path.stem
                self.create_agent_tasks(task_id)
            
            # Wait for completion signal (task moved to DONE)
            while not self.is_task_completed(task_path.stem):
                time.sleep(5)
            
            print(f"Task completed: {task_path.name}")

if __name__ == "__main__":
    orchestrator = TaskOrchestrator()
    orchestrator.run()