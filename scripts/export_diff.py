import os
import subprocess
import json

def load_sessions(sessions_dir):
    sessions = []
    for entry in os.listdir(sessions_dir):
        session_path = os.path.join(sessions_dir, entry)
        if os.path.isdir(session_path) and os.path.exists(os.path.join(session_path, 'session.json')):
            with open(os.path.join(session_path, 'session.json'), 'r') as file:
                sessions.append((entry, json.load(file)))
    return sessions

def display_sessions(sessions):
    for idx, (session_id, session_data) in enumerate(sessions, start=1):
        print(f"{idx}. {session_id} - {session_data['task_title']}")

def get_user_choice(sessions):
    while True:
        try:
            choice = int(input("Enter the number of the session to export diff for: "))
            if 1 <= choice <= len(sessions):
                return sessions[choice - 1]
            else:
                print(f"Invalid choice. Please enter a number between 1 and {len(sessions)}.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")

def verify_git_repository(repo_path):
    try:
        subprocess.run(['git', '-C', repo_path, 'rev-parse', '--is-inside-work-tree'], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def export_diff(session_path, repo_path):
    diff_output = subprocess.run(['git', '-C', repo_path, 'diff'], capture_output=True, text=True).stdout
    with open(os.path.join(session_path, 'diff.patch'), 'w') as file:
        file.write(diff_output)
    if not diff_output.strip():
        print("No changes detected. Created an empty diff.patch.")
    else:
        print("Diff exported successfully.")

def main():
    sessions_dir = 'sessions'
    if not os.path.exists(sessions_dir):
        print(f"Error: No sessions directory found at {sessions_dir}.")
        return

    sessions = load_sessions(sessions_dir)
    if not sessions:
        print("No sessions available for diff export.")
        return

    display_sessions(sessions)
    session_id, session_data = get_user_choice(sessions)

    repo_path = session_data['repo_path']
    if not os.path.exists(repo_path):
        print(f"Error: Repository path {repo_path} does not exist.")
        return
    if not verify_git_repository(repo_path):
        print(f"Error: {repo_path} is not a valid git repository.")
        return

    export_diff(os.path.join(sessions_dir, session_id), repo_path)

    print(f"Diff exported for session {session_id} successfully.")

if __name__ == "__main__":
    main()
