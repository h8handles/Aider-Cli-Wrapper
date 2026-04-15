import subprocess
from pathlib import Path

from scripts.session_utils import (
    list_changed_files,
    load_sessions as load_session_records,
    save_session_record,
)


ROOT_DIR = Path(__file__).resolve().parent.parent
SESSIONS_DIR = ROOT_DIR / "sessions"


def load_sessions(sessions_dir: str | Path):
    return load_session_records(Path(sessions_dir))


def display_sessions(sessions) -> None:
    for idx, (session_id, session_data) in enumerate(sessions, start=1):
        print(f"{idx}. {session_id} - {session_data.task_title}")


def get_user_choice(sessions):
    while True:
        try:
            choice = int(input("Enter the number of the session to export diff for: "))
            if 1 <= choice <= len(sessions):
                return sessions[choice - 1]
            print(f"Invalid choice. Please enter a number between 1 and {len(sessions)}.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")


def verify_git_repository(repo_path: str | Path) -> bool:
    try:
        subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "--is-inside-work-tree"],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def export_diff(session_path: str | Path, repo_path: str | Path, session_data=None) -> None:
    session_dir = Path(session_path)
    repo_dir = Path(repo_path)
    diff_output = subprocess.run(
        ["git", "-C", str(repo_dir), "diff", "--stat", "--patch"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout

    (session_dir / "diff.patch").write_text(diff_output, encoding="utf-8")

    # This keeps the review artifact aligned with the actual diff snapshot at export time.
    if session_data is not None:
        session_data.changed_files = list_changed_files(repo_dir)
        save_session_record(session_dir, session_data)

    if not diff_output.strip():
        print("No changes detected. Created an empty diff.patch.")
    else:
        print("Diff exported successfully.")


def main() -> None:
    if not SESSIONS_DIR.exists():
        print(f"Error: No sessions directory found at {SESSIONS_DIR}.")
        return

    sessions = load_sessions(SESSIONS_DIR)
    if not sessions:
        print("No sessions available for diff export.")
        return

    display_sessions(sessions)
    session_id, session_data = get_user_choice(sessions)

    repo_path = Path(session_data.repo_path)
    if not repo_path.exists():
        print(f"Error: Repository path {repo_path} does not exist.")
        return
    if not verify_git_repository(repo_path):
        print(f"Error: {repo_path} is not a valid git repository.")
        return

    export_diff(SESSIONS_DIR / session_id, repo_path, session_data)
    print(f"Diff exported for session {session_id} successfully.")


if __name__ == "__main__":
    main()
