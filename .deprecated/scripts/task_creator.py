import os
import sys
from pathlib import Path
from datetime import datetime

def create_task(task_id, description):
    """Create a new task in the TODO directory"""
    root_dir = Path(os.getcwd())
    todo_dir = root_dir / "TASKS" / "TODO"
    
    # Create directory if it doesn't exist
    todo_dir.mkdir(parents=True, exist_ok=True)
    
    # Create task file
    task_path = todo_dir / f"{task_id}.md"
    
    task_content = f"""---
task_id: {task_id}
created: {datetime.now().isoformat()}
status: pending
---

# Task: {task_id}

## Description
{description}

## Requirements
- Implement the functionality as described
- Write appropriate tests
- Document usage
- Ensure code quality

## Acceptance Criteria
- All requirements implemented
- Tests passing
- Documentation complete
"""
    
    with open(task_path, "w") as f:
        f.write(task_content)
    
    print(f"Task created: {task_path}")
    return task_path

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python task_creator.py <task_id> <description>")
        sys.exit(1)
    
    task_id = sys.argv[1]
    description = sys.argv[2]
    
    create_task(task_id, description)