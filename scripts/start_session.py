from datetime import datetime
from pathlib import Path

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
    try:
        return read_json(template_path)
    except FileNotFoundError:
        print(f"Error: Template file {template_path} not found.")
        raise SystemExit(1) from None


def sanitize_expected_scope(expected_scope_input: str) -> list[str]:
    return normalize_scope_entries(expected_scope_input)


def create_session_folder(base_dir: str | Path, session_id: str) -> str:
    session_path = Path(base_dir) / session_id
    session_path.mkdir(parents=True, exist_ok=False)
    return str(session_path)


def write_file(file_path: str | Path, content: str) -> None:
    Path(file_path).write_text(content, encoding="utf-8")


def load_rules() -> list[str]:
    if not RULES_PATH.exists():
        return []

    # This extracts checklist bullets so the wrapper can feed aider a stable guardrail prompt.
    return parse_simple_yaml_list(RULES_PATH)


def build_session_record(task_title: str, task_type: str, expected_scope: list[str], model_name: str) -> SessionRecord:
    timestamp = datetime.now().isoformat(timespec="seconds")
    repo_path = ROOT_DIR.resolve()
    session_id = f"{timestamp[:10]}_{timestamp[11:13]}{timestamp[14:16]}{timestamp[17:19]}_{normalize_task_name(task_title)}"
    prompt_preview = build_prompt_preview(expected_scope, load_rules())

    return SessionRecord(
        session_id=session_id,
        timestamp=timestamp,
        repo_name=repo_path.name,
        repo_path=str(repo_path),
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
    # These starter files make each session folder immediately usable by the wrapper and reviewer.
    save_session_record(session_path, session)
    write_file(session_path / "prompt.txt", session.prompt_preview)
    write_file(session_path / "context_files.txt", "\n".join(session.expected_scope))
    write_file(session_path / "notes.txt", "")


def create_session(task_title: str, task_type: str, expected_scope_input: str, model_name: str) -> tuple[Path, SessionRecord]:
    load_template()
    expected_scope = sanitize_expected_scope(expected_scope_input)
    session = build_session_record(task_title=task_title, task_type=task_type, expected_scope=expected_scope, model_name=model_name)

    ensure_directory(SESSIONS_DIR)
    session_path = Path(create_session_folder(SESSIONS_DIR, session.session_id))
    initialize_session_files(session_path, session)

    return session_path, session


def prompt_for_session_inputs() -> tuple[str, str, str, str]:
    task_title = input("Enter the task title: ").strip()
    task_type = input("Enter the task type (optional, default is general): ").strip() or "general"
    expected_scope_input = input("Enter the expected scope as a comma separated list (optional): ").strip()
    model_name = input("Enter the model name (optional): ").strip()
    return task_title, task_type, expected_scope_input, model_name


def main() -> None:
    task_title, task_type, expected_scope_input, model_name = prompt_for_session_inputs()
    session_path, _ = create_session(task_title, task_type, expected_scope_input, model_name)

    print(f"Session created at: {session_path}")


if __name__ == "__main__":
    main()
