import os
import json
from datetime import datetime

def load_template(template_path):
    try:
        with open(template_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: Template file {template_path} not found.")
        exit(1)

def normalize_task_name(task_title):
    # Remove special characters and replace spaces with underscores
    return ''.join(c if c.isalnum() or c == '_' else '_' for c in task_title).lower()

def sanitize_expected_scope(expected_scope_input):
    import re

    # Split by commas and trim whitespace
    entries = [entry.strip() for entry in expected_scope_input.split(',')]

    # Normalize repeated spaces
    entries = [re.sub(r'\s+', ' ', entry) for entry in entries]

    # Remove non-ASCII or unexpected Unicode characters
    entries = [re.sub(r'[^a-zA-Z0-9_\-/\\.]', '', entry) for entry in entries]

    # Convert backslashes to forward slashes
    entries = [entry.replace('\\', '/') for entry in entries]

    # Discard empty entries
    entries = [entry for entry in entries if entry]

    return entries

def create_session_folder(base_dir, session_id):
    session_path = os.path.join(base_dir, session_id)
    try:
        os.makedirs(session_path)
        return session_path
    except FileExistsError:
        print(f"Error: Session folder {session_path} already exists.")
        exit(1)

def write_file(file_path, content):
    with open(file_path, 'w') as file:
        file.write(content)

def main():
    template = load_template('templates/session_template.json')

    repo_name = os.path.basename(os.getcwd())
    repo_path = os.getcwd()
    task_title = input("Enter the task title: ").strip()
    task_type = input("Enter the task type (optional, default is general): ").strip() or "general"
    expected_scope_input = input("Enter the expected scope as a comma separated list (optional): ").strip()
    model_name = input("Enter the model name (optional): ").strip()

    timestamp = datetime.now().isoformat()
    session_id = f"{timestamp[:10]}_{timestamp[11:13]}{timestamp[14:16]}{timestamp[17:19]}_{normalize_task_name(task_title)}"

    if not os.path.exists('sessions'):
        os.makedirs('sessions')

    session_path = create_session_folder('sessions', session_id)

    expected_scope = sanitize_expected_scope(expected_scope_input)

    template.update({
        "session_id": session_id,
        "timestamp": timestamp,
        "repo_name": repo_name,
        "repo_path": repo_path,
        "task_title": task_title,
        "task_type": task_type,
        "agent_name": "aider",
        "model_name": model_name,
        "expected_scope": expected_scope,
        "failure_tags": [],
        "changed_files": [],
        "verdict": None,
        "score": None,
        "notes_summary": ""
    })

    write_file(os.path.join(session_path, 'session.json'), json.dumps(template, indent=4))
    write_file(os.path.join(session_path, 'prompt.txt'), "")
    write_file(os.path.join(session_path, 'context_files.txt'), "")
    write_file(os.path.join(session_path, 'notes.txt'), "")

    print(f"Session created at: {session_path}")

if __name__ == "__main__":
    main()
