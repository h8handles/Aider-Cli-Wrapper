import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from time import perf_counter

from scripts.session_utils import load_session_record, load_sessions as load_session_records, save_session_record


ROOT_DIR = Path(__file__).resolve().parent.parent
SESSIONS_DIR = ROOT_DIR / "sessions"
DEFAULT_CONFIG_PATH = ROOT_DIR / ".aider.config.yaml"


def load_sessions(sessions_dir: str | Path):
    return load_session_records(Path(sessions_dir))


def display_sessions(sessions) -> None:
    for idx, (session_id, session_data) in enumerate(sessions, start=1):
        print(f"{idx}. {session_id} - {session_data.task_title}")


def get_user_choice(sessions):
    while True:
        try:
            choice = int(input("Enter the number of the session to run with aider: "))
            if 1 <= choice <= len(sessions):
                return sessions[choice - 1]
            print(f"Invalid choice. Please enter a number between 1 and {len(sessions)}.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")


def resolve_aider_executable() -> str | None:
    for candidate in ("aider", "aider.exe", "aider.cmd"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def get_message_argument(session_dir: Path, session_data) -> list[str]:
    prompt_path = session_dir / "prompt.txt"
    if prompt_path.exists():
        prompt_text = prompt_path.read_text(encoding="utf-8").strip()
        if prompt_text:
            return ["--message-file", str(prompt_path)]

    # Older sessions may not have a populated prompt file, so fall back to the task title.
    if session_data.task_title.strip():
        return ["--message", session_data.task_title.strip()]

    raise ValueError("Session does not contain a usable prompt or task title.")


def validate_expected_scope(repo_path: Path, expected_scope: list[str]) -> list[str]:
    missing_files: list[str] = []
    for relative_path in expected_scope:
        if not (repo_path / relative_path).exists():
            missing_files.append(relative_path)
    return missing_files


def build_aider_command(aider_executable: str, config_path: Path, session_dir: Path, session_data, model_override: str = "") -> list[str]:
    if not config_path.exists():
        raise FileNotFoundError(f"Required aider config file was not found: {config_path}")

    command = [aider_executable, "--config", str(config_path)]
    selected_model = model_override.strip() or session_data.model_name.strip()
    if selected_model:
        command.extend(["--model", selected_model])

    command.extend(get_message_argument(session_dir, session_data))
    command.extend(session_data.expected_scope)
    return command


def save_run_artifacts(session_dir: Path, artifact_payload: dict, stdout_text: str, stderr_text: str) -> None:
    # These files keep the raw aider invocation easy to inspect after the run finishes.
    (session_dir / "aider_run.json").write_text(json.dumps(artifact_payload, indent=2) + "\n", encoding="utf-8")
    (session_dir / "aider_stdout.txt").write_text(stdout_text, encoding="utf-8")
    (session_dir / "aider_stderr.txt").write_text(stderr_text, encoding="utf-8")


def run_session(session_dir: Path, session_data, model_override: str = "") -> int:
    repo_path = Path(session_data.repo_path)
    if not repo_path.exists():
        print(f"Error: Repository path does not exist: {repo_path}")
        return 2

    missing_scope_files = validate_expected_scope(repo_path, session_data.expected_scope)
    if missing_scope_files:
        print(f"Error: Expected scope file(s) were not found: {', '.join(missing_scope_files)}")
        return 2

    aider_executable = resolve_aider_executable()
    if not aider_executable:
        print("Error: Could not find the 'aider' executable on PATH.")
        return 127

    try:
        command = build_aider_command(aider_executable, DEFAULT_CONFIG_PATH, session_dir, session_data, model_override=model_override)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}")
        return 2

    started_at = datetime.now().isoformat(timespec="seconds")
    timer_start = perf_counter()
    try:
        result = subprocess.run(
            command,
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        stdout_text = result.stdout
        stderr_text = result.stderr
        exit_code = result.returncode
    except OSError as exc:
        stdout_text = ""
        stderr_text = str(exc)
        exit_code = 127

    finished_at = datetime.now().isoformat(timespec="seconds")
    duration_seconds = round(perf_counter() - timer_start, 3)

    artifact_payload = {
        "command": command,
        "exit_code": exit_code,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": duration_seconds,
        "cwd": str(repo_path),
    }
    save_run_artifacts(session_dir, artifact_payload, stdout_text, stderr_text)

    session_data.last_run_command = command
    session_data.last_run_exit_code = exit_code
    session_data.last_run_started_at = started_at
    session_data.last_run_finished_at = finished_at
    session_data.last_run_duration_seconds = duration_seconds
    if model_override.strip():
        session_data.model_name = model_override.strip()
    save_session_record(session_dir, session_data)

    if exit_code == 0:
        print("Aider run completed successfully.")
    else:
        print(f"Aider run failed with exit code {exit_code}. See session artifacts for details.")
    return exit_code


def main() -> int:
    if not SESSIONS_DIR.exists():
        print(f"Error: No sessions directory found at {SESSIONS_DIR}.")
        return 2

    sessions = load_sessions(SESSIONS_DIR)
    if not sessions:
        print("Error: No sessions are available. Create a session first with start_session.py.")
        return 2

    display_sessions(sessions)
    session_id, _ = get_user_choice(sessions)
    session_dir = SESSIONS_DIR / session_id
    session_data = load_session_record(session_dir)

    model_override = input("Enter a model override (optional, leave blank to use the stored session model): ").strip()
    return run_session(session_dir, session_data, model_override=model_override)


if __name__ == "__main__":
    raise SystemExit(main())
