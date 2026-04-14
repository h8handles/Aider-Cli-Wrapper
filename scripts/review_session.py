import os
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
            choice = int(input("Enter the number of the session to review: "))
            if 1 <= choice <= len(sessions):
                return sessions[choice - 1]
            else:
                print(f"Invalid choice. Please enter a number between 1 and {len(sessions)}.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")

def display_session_details(session_data):
    print("\nSession Details:")
    print(f"Session ID: {session_data['session_id']}")
    print(f"Task Title: {session_data['task_title']}")
    print(f"Task Type: {session_data['task_type']}")
    print(f"Repo Name: {session_data['repo_name']}")
    print(f"Expected Scope: {', '.join(session_data['expected_scope']) if session_data['expected_scope'] else 'N/A'}")
    print(f"Current Verdict: {session_data['verdict'] or 'None'}")
    print(f"Current Score: {session_data['score'] or 'None'}")
    print(f"Current Failure Tags: {', '.join(session_data['failure_tags']) if session_data['failure_tags'] else 'N/A'}")
    print(f"Current Notes Summary: {session_data['notes_summary'] or 'N/A'}\n")

def get_user_input():
    verdict = input("Enter the verdict (accepted, accepted_with_edits, rejected): ").strip().lower()
    allowed_verdicts = ["accepted", "accepted_with_edits", "rejected"]
    while verdict not in allowed_verdicts:
        print(f"Invalid verdict. Please choose from {', '.join(allowed_verdicts)}.")
        verdict = input("Enter the verdict: ").strip().lower()

    score = input("Enter the score (0-5): ").strip()
    while not score.isdigit() or not 0 <= int(score) <= 5:
        print("Invalid score. Please enter an integer between 0 and 5.")
        score = input("Enter the score: ").strip()

    failure_tags_input = input("Enter the failure tags as a comma separated list (optional): ").strip()
    failure_tags = [tag.strip() for tag in failure_tags_input.split(',') if tag.strip()] if failure_tags_input else []

    notes_summary = input("Enter the notes summary (optional): ").strip()

    return verdict, int(score), failure_tags, notes_summary

def update_session(session_path, verdict, score, failure_tags, notes_summary):
    with open(os.path.join(session_path, 'session.json'), 'r') as file:
        session_data = json.load(file)

    session_data.update({
        "verdict": verdict,
        "score": score,
        "failure_tags": failure_tags,
        "notes_summary": notes_summary
    })

    with open(os.path.join(session_path, 'session.json'), 'w') as file:
        json.dump(session_data, file, indent=4)

def main():
    sessions_dir = 'sessions'
    if not os.path.exists(sessions_dir):
        print(f"Error: No sessions directory found at {sessions_dir}.")
        return

    sessions = load_sessions(sessions_dir)
    if not sessions:
        print("No sessions available for review.")
        return

    display_sessions(sessions)
    session_id, session_data = get_user_choice(sessions)

    display_session_details(session_data)

    verdict, score, failure_tags, notes_summary = get_user_input()

    update_session(os.path.join(sessions_dir, session_id), verdict, score, failure_tags, notes_summary)

    print(f"Session {session_id} reviewed and updated successfully.")

if __name__ == "__main__":
    main()
