from pathlib import Path

from scripts.session_utils import (
    VERDICTS,
    load_session_record,
    load_sessions as load_session_records,
    normalize_tag_entries,
    parse_simple_yaml_list,
    save_session_record,
)


ROOT_DIR = Path(__file__).resolve().parent.parent
SESSIONS_DIR = ROOT_DIR / "sessions"
FAILURE_TAGS_PATH = ROOT_DIR / "config" / "failure_tags.yaml"


def load_sessions(sessions_dir: str | Path):
    """Load all saved sessions available for review."""
    return load_session_records(Path(sessions_dir))


def display_sessions(sessions) -> None:
    """Print the list of sessions that can be reviewed."""
    for idx, (session_id, session_data) in enumerate(sessions, start=1):
        print(f"{idx}. {session_id} - {session_data.task_title}")


def get_user_choice(sessions):
    """Prompt until the user selects a valid session number to review."""
    while True:
        try:
            choice = int(input("Enter the number of the session to review: "))
            if 1 <= choice <= len(sessions):
                return sessions[choice - 1]
            print(f"Invalid choice. Please enter a number between 1 and {len(sessions)}.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")


def display_session_details(session_data) -> None:
    """Print the key session metadata reviewers need before entering a verdict."""
    print("\nSession Details:")
    print(f"Session ID: {session_data.session_id}")
    print(f"Task Title: {session_data.task_title}")
    print(f"Task Type: {session_data.task_type}")
    print(f"Repo Name: {session_data.repo_name}")
    print(f"Expected Scope: {', '.join(session_data.expected_scope) if session_data.expected_scope else 'N/A'}")
    print(f"Changed Files: {', '.join(session_data.changed_files) if session_data.changed_files else 'N/A'}")
    print(f"Current Verdict: {session_data.verdict or 'None'}")
    print(f"Current Score: {session_data.score if session_data.score is not None else 'None'}")
    print(f"Current Failure Tags: {', '.join(session_data.failure_tags) if session_data.failure_tags else 'N/A'}")
    print(f"Current Notes Summary: {session_data.notes_summary or 'N/A'}\n")


def load_allowed_failure_tags() -> set[str]:
    """Load the configured failure tags that reviewers are allowed to assign."""
    return set(parse_simple_yaml_list(FAILURE_TAGS_PATH))


def prompt_for_failure_tags() -> list[str]:
    """Prompt for failure tags and reject values outside the configured allowlist."""
    allowed_tags = load_allowed_failure_tags()
    while True:
        failure_tags_input = input("Enter the failure tags as a comma separated list (optional): ").strip()
        failure_tags = normalize_tag_entries(failure_tags_input)
        invalid_tags = [tag for tag in failure_tags if allowed_tags and tag not in allowed_tags]
        if not invalid_tags:
            return failure_tags
        print(f"Invalid failure tags: {', '.join(invalid_tags)}. Allowed tags: {', '.join(sorted(allowed_tags))}.")


def get_user_input():
    """Collect a validated review verdict, score, tags, and optional notes summary."""
    verdict = input(f"Enter the verdict ({', '.join(VERDICTS)}): ").strip().lower()
    while verdict not in VERDICTS:
        print(f"Invalid verdict. Please choose from {', '.join(VERDICTS)}.")
        verdict = input("Enter the verdict: ").strip().lower()

    score = input("Enter the score (0-5): ").strip()
    while not score.isdigit() or not 0 <= int(score) <= 5:
        print("Invalid score. Please enter an integer between 0 and 5.")
        score = input("Enter the score: ").strip()

    failure_tags = prompt_for_failure_tags()
    notes_summary = input("Enter the notes summary (optional): ").strip()

    return verdict, int(score), failure_tags, notes_summary


def update_session(session_path: str | Path, verdict: str, score: int, failure_tags: list[str], notes_summary: str) -> None:
    """Persist review fields back to the selected session's metadata file."""
    session_dir = Path(session_path)
    session_data = load_session_record(session_dir)
    session_data.verdict = verdict
    session_data.score = score
    session_data.failure_tags = failure_tags
    session_data.notes_summary = notes_summary.strip()
    save_session_record(session_dir, session_data)


def main() -> None:
    """Run the interactive review flow for an existing session."""
    if not SESSIONS_DIR.exists():
        print(f"Error: No sessions directory found at {SESSIONS_DIR}.")
        return

    sessions = load_sessions(SESSIONS_DIR)
    if not sessions:
        print("No sessions available for review.")
        return

    display_sessions(sessions)
    session_id, session_data = get_user_choice(sessions)
    display_session_details(session_data)

    verdict, score, failure_tags, notes_summary = get_user_input()
    update_session(SESSIONS_DIR / session_id, verdict, score, failure_tags, notes_summary)

    print(f"Session {session_id} reviewed and updated successfully.")


if __name__ == "__main__":
    main()
