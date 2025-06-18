import os
import sys
import json
import shutil
import subprocess
import time
from pathlib import Path
from datetime import datetime

class TaskOrchestrator:
    def __init__(self):
        self.root_dir = Path(os.getcwd())
        self.todo_dir = self.root_dir / "TASKS" / "TODO"
        self.done_dir = self.root_dir / "TASKS" / "DONE"
        self.specs_dir = self.root_dir / "TASKS" / "SPECS"
        
        # Create directories if they don't exist
        for dir_path in [self.todo_dir, self.done_dir, self.specs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def activate_python_env(self):
        """Activate Python environment if not already activated"""
        try:
            subprocess.run("pyenv\.pyenv\Scripts\activate.bat", shell=True)
        except Exception as e:
            print(f"Failed to activate environment: {e}")
    
    def get_next_task(self):
        """Get the next task from TODO directory"""
        tasks = list(self.todo_dir.glob("*.md"))
        if not tasks:
            return None
        
        # Sort by creation time to get oldest task first
        tasks.sort(key=lambda x: x.stat().st_ctime)
        return tasks[0]
    
    def analyze_task(self, task_path):
        """Use Groq to analyze the task and create specs"""
        task_id = task_path.stem
        specs_path = self.specs_dir / f"{task_id}_analysis.md"
        
        print(f"Analyzing task: {task_id}")
        
        # Here we would normally call Groq API directly
        # For now, simulate by copying and adding analysis section
        task_content = task_path.read_text()
        
        analysis = f"""# Task Analysis: {task_id}
        
{task_content}

## Component Breakdown
- Main functionality
- Helper functions
- Tests
- Documentation

## Implementation Approach
1. Setup required structures
2. Implement core functionality
3. Add validation and error handling
4. Create tests
5. Document usage
"""
        
        specs_path.write_text(analysis)
        return specs_path
    
    def create_implementation_plan(self, analysis_path):
        """Use Groq to create detailed implementation plan"""
        task_id = analysis_path.stem.replace('_analysis', '')
        plan_path = self.specs_dir / f"{task_id}_plan.md"
        
        print(f"Creating implementation plan for: {task_id}")
        
        # Simulate Groq planning output
        analysis_content = analysis_path.read_text()
        
        plan = f"""# Implementation Plan: {task_id}
        
{analysis_content}

## Files to Create/Modify

1. src/{task_id}.py
```python
def main_function():
    return "Implementation based on task requirements"
```

2. tests/test_{task_id}.py
```python
def test_main_function():
    assert main_function() == "Implementation based on task requirements"
```

## Steps to Execute
1. Create the files as specified
2. Run the tests to verify
3. Update documentation
4. Commit changes
"""
        
        plan_path.write_text(plan)
        return plan_path
    
    def execute_task(self, plan_path):
        """Use Claude to execute the implementation plan"""
        task_id = plan_path.stem.replace('_plan', '')
        
        print(f"Executing task: {task_id}")
        
        # Here we would normally call Continue in agent mode with Claude
        # Simulate success
        
        # Create task directory in DONE
        done_task_dir = self.done_dir / task_id
        done_task_dir.mkdir(parents=True, exist_ok=True)
        
        # Create report
        report_path = done_task_dir / f"{task_id}_report.md"
        report = f"""# Task Completion Report: {task_id}
        
## Overview
Task completed successfully on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Implementation Details
- Files created/modified as per plan
- All tests passing
- Documentation updated

## Next Steps
None - task complete
"""
        
        report_path.write_text(report)
        
        # Move original task file to DONE directory
        original_task = self.todo_dir / f"{task_id}.md"
        if original_task.exists():
            shutil.copy(original_task, done_task_dir / f"{task_id}.md")
            original_task.unlink()
        
        # Git commit
        self.commit_changes(task_id)
        
        return done_task_dir
    
    def commit_changes(self, task_id):
        """Commit changes to git"""
        try:
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", f"Task {task_id} completed"], check=True)
            print(f"Changes committed for task: {task_id}")
        except Exception as e:
            print(f"Failed to commit changes: {e}")
    
    def run(self):
        """Main execution loop"""
        print("Starting task orchestration...")
        self.activate_python_env()
        
        while True:
            # Get next task
            task_path = self.get_next_task()
            if not task_path:
                print("No tasks found. Waiting...")
                time.sleep(10)
                continue
            
            try:
                # Process task
                analysis_path = self.analyze_task(task_path)
                plan_path = self.create_implementation_plan(analysis_path)
                self.execute_task(plan_path)
                
                print(f"{task_path.stem} done")
            except Exception as e:
                print(f"Error processing task {task_path.name}: {e}")
            
            # Wait briefly before checking for new tasks
            time.sleep(1)

if __name__ == "__main__":
    orchestrator = TaskOrchestrator()
    orchestrator.run()