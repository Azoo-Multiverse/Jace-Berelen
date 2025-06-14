import subprocess
import sys
import os

# Paths
BASE_DIR = '.' #os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = '.' #os.path.abspath(os.path.join(BASE_DIR, "../JACE"))

def git_commit_and_push(message):
    try:
        subprocess.run(f'git -C "{PROJECT_DIR}" add .', check=True, shell=True)
        subprocess.run(f'git -C "{PROJECT_DIR}" commit -m "{message}"', check=True, shell=True)
        subprocess.run(f'git -C "{PROJECT_DIR}" push', check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Git error: {e}")

if __name__ == "__main__":
    commit_message = ".."
    if len(sys.argv) > 1:
        commit_message = sys.argv[1]
    git_commit_and_push(commit_message)