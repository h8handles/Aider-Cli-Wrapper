from datetime import datetime
from pathlib import Path
import subprocess

from scripts.session_utils import (
    SessionRecord,
    build_prompt_preview,
    ensure_directory,
    normalize_scope_entries,
    normalize_task_name,
    parse_simple_yaml_list,
    read_json,
    save_session_record,
)


ROOT_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = ROOT_DIR / "templates" / "session_template.json"
SESSIONS_DIR = ROOT_DIR / "sessions"
RULES_PATH = ROOT_DIR / "config" / "global_rules.md"


def load_template(template_path: Path = TEMPLATE_PATH) -> dict:
    """Load the session template file used to validate startup configuration."""
    try:
        return read_json(template_path)
    except FileNotFoundError:
        print(f"Error: Template file {template_path} not found.")
        raise SystemExit(1) from None


def sanitize_expected_scope(expected_scope_input: str) -> list[str]:
    """Normalize the raw expected-scope input into distinct relative paths."""
    return normalize_scope_entries(expected_scope_input)


def create_session_folder(base_dir: str | Path, session_id: str) -> str:
    """Create the on-disk folder for a new session and return its path as a string."""
    session_path = Path(base_dir) / session_id
    session_path.mkdir(parents=True, exist_ok=False)
    return str(session_path)


def write_file(file_path: str | Path, content: str) -> None:
    """Write UTF-8 text content to a file used by a session artifact."""
    Path(file_path).write_text(content, encoding="utf-8")


def load_rules() -> list[str]:
    """Load global wrapper rules that should appear in a session prompt preview."""
    if not RULES_PATH.exists():
        return []

    # This extracts checklist bullets so the wrapper can feed aider a stable guardrail prompt.
    return parse_simple_yaml_list(RULES_PATH)


def get_repo_baseline_commit(repo_path: Path) -> str:
    """Resolve the current HEAD commit used as the session's diff baseline."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise OSError(f"Could not determine the git baseline for {repo_path}.") from exc

    baseline_commit_sha = result.stdout.strip()
    if not baseline_commit_sha:
        raise OSError(f"Could not determine the git baseline for {repo_path}.")
    return baseline_commit_sha


def build_session_record(
    task_title: str,
    task_type: str,
    expected_scope: list[str],
    model_name: str,
    baseline_commit_sha: str,
) -> SessionRecord:
    """Construct the initial session metadata persisted at creation time."""
    timestamp = datetime.now().isoformat(timespec="seconds")
    repo_path = ROOT_DIR.resolve()
    session_id = f"{timestamp[:10]}_{timestamp[11:13]}{timestamp[14:16]}{timestamp[17:19]}_{normalize_task_name(task_title)}"
    prompt_preview = build_prompt_preview(expected_scope, load_rules())

    return SessionRecord(
        session_id=session_id,
        timestamp=timestamp,
        repo_name=repo_path.name,
        repo_path=str(repo_path),
        baseline_commit_sha=baseline_commit_sha,
        task_title=task_title,
        task_type=task_type or "general",
        agent_name="aider",
        model_name=model_name,
        expected_scope=expected_scope,
        verdict=None,
        score=None,
        failure_tags=[],
        changed_files=[],
        notes_summary="",
        prompt_preview=prompt_preview,
        last_run_command=[],
        last_run_exit_code=None,
        last_run_started_at="",
        last_run_finished_at="",
        last_run_duration_seconds=None,
    )


def initialize_session_files(session_path: Path, session: SessionRecord) -> None:
    """Write the initial session artifacts needed for later run/review/export steps."""
    # These starter files make each session folder immediately usable by the wrapper and reviewer.
    save_session_record(session_path, session)
    write_file(session_path / "prompt.txt", session.prompt_preview)
    write_file(session_path / "context_files.txt", "\n".join(session.expected_scope))
    write_file(session_path / "notes.txt", "")


def create_session(task_title: str, task_type: str, expected_scope_input: str, model_name: str) -> tuple[Path, SessionRecord]:
    """Create a new session directory and persist its initial metadata and prompt files."""
    load_template()
    expected_scope = sanitize_expected_scope(expected_scope_input)
    baseline_commit_sha = get_repo_baseline_commit(ROOT_DIR.resolve())
    session = build_session_record(
        task_title=task_title,
        task_type=task_type,
        expected_scope=expected_scope,
        model_name=model_name,
        baseline_commit_sha=baseline_commit_sha,
    )

    ensure_directory(SESSIONS_DIR)
    session_path = Path(create_session_folder(SESSIONS_DIR, session.session_id))
    initialize_session_files(session_path, session)

    return session_path, session


def prompt_for_session_inputs() -> tuple[str, str, str, str]:
    """Collect the interactive inputs required to create a new session."""
    task_title = input("Enter the task title: ").strip()
    task_type = input("Enter the task type (optional, default is general): ").strip() or "general"
    expected_scope_input = input("Enter the expected scope as a comma separated list (optional): ").strip()
    model_name = input("Enter the model name (optional): ").strip()
    return task_title, task_type, expected_scope_input, model_name


def main() -> None:
    """Run the interactive session-creation flow and print the created path."""
    task_title, task_type, expected_scope_input, model_name = prompt_for_session_inputs()
    session_path, _ = create_session(task_title, task_type, expected_scope_input, model_name)

    print(f"Session created at: {session_path}")


if __name__ == "__main__":
    main()
