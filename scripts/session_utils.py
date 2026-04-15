import json
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path


VERDICTS = ("accepted", "accepted_with_edits", "rejected")


@dataclass
class SessionRecord:
    """Structured session metadata persisted to each session's ``session.json`` file."""
    session_id: str
    timestamp: str
    repo_name: str
    repo_path: str
    baseline_commit_sha: str
    task_title: str
    task_type: str
    agent_name: str
    model_name: str
    expected_scope: list[str] = field(default_factory=list)
    verdict: str | None = None
    score: int | None = None
    failure_tags: list[str] = field(default_factory=list)
    changed_files: list[str] = field(default_factory=list)
    notes_summary: str = ""
    prompt_preview: str = ""
    last_run_command: list[str] = field(default_factory=list)
    last_run_exit_code: int | None = None
    last_run_started_at: str = ""
    last_run_finished_at: str = ""
    last_run_duration_seconds: float | None = None

    # This keeps older session.json files usable while normalizing new writes.
    @classmethod
    def from_dict(cls, data: dict) -> "SessionRecord":
        """Build a normalized session record from stored JSON data."""
        return cls(
            session_id=data.get("session_id", ""),
            timestamp=data.get("timestamp", ""),
            repo_name=data.get("repo_name", ""),
            repo_path=data.get("repo_path", ""),
            baseline_commit_sha=(data.get("baseline_commit_sha") or "").strip(),
            task_title=data.get("task_title", ""),
            task_type=data.get("task_type", "general"),
            agent_name=data.get("agent_name", "aider"),
            model_name=data.get("model_name", ""),
            expected_scope=normalize_scope_entries(data.get("expected_scope", [])),
            verdict=data.get("verdict") or None,
            score=data.get("score") if data.get("score") is not None else None,
            failure_tags=normalize_tag_entries(data.get("failure_tags", [])),
            changed_files=normalize_scope_entries(data.get("changed_files", [])),
            notes_summary=(data.get("notes_summary") or "").strip(),
            prompt_preview=(data.get("prompt_preview") or "").strip(),
            last_run_command=[str(part) for part in data.get("last_run_command", [])],
            last_run_exit_code=data.get("last_run_exit_code") if data.get("last_run_exit_code") is not None else None,
            last_run_started_at=(data.get("last_run_started_at") or "").strip(),
            last_run_finished_at=(data.get("last_run_finished_at") or "").strip(),
            last_run_duration_seconds=data.get("last_run_duration_seconds") if data.get("last_run_duration_seconds") is not None else None,
        )

    def to_dict(self) -> dict:
        """Convert the session record back to plain JSON-serializable data."""
        return asdict(self)


def read_json(path: Path) -> dict:
    """Read a UTF-8 JSON file and return its parsed object."""
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, data: dict) -> None:
    """Write JSON data with stable indentation and a trailing newline."""
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)
        file.write("\n")


def ensure_directory(path: Path) -> Path:
    """Create a directory tree if needed and return the resolved path object."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_session_record(session_dir: Path) -> SessionRecord:
    """Load one session record from ``session.json`` inside a session directory."""
    return SessionRecord.from_dict(read_json(session_dir / "session.json"))


def save_session_record(session_dir: Path, session: SessionRecord) -> None:
    """Persist a session record back to the session's ``session.json`` file."""
    write_json(session_dir / "session.json", session.to_dict())


def load_sessions(sessions_dir: Path) -> list[tuple[str, SessionRecord]]:
    """Load all sessions from a sessions directory in reverse-sorted folder order."""
    sessions: list[tuple[str, SessionRecord]] = []
    if not sessions_dir.exists():
        return sessions

    for session_dir in sorted(sessions_dir.iterdir(), reverse=True):
        session_file = session_dir / "session.json"
        if session_dir.is_dir() and session_file.exists():
            sessions.append((session_dir.name, load_session_record(session_dir)))
    return sessions


def normalize_task_name(task_title: str) -> str:
    """Convert a task title into a filesystem-friendly slug fragment."""
    cleaned = "".join(character if character.isalnum() else "_" for character in task_title.lower())
    return cleaned.strip("_") or "task"


def normalize_scope_entries(raw_scope: str | list[str]) -> list[str]:
    """Normalize expected-scope or changed-file entries into clean relative paths."""
    entries = raw_scope.split(",") if isinstance(raw_scope, str) else raw_scope
    normalized: list[str] = []

    for entry in entries:
        compact = " ".join(str(entry).strip().split())
        if not compact:
            continue
        candidate = compact.replace("\\", "/")
        candidate = "".join(character for character in candidate if character.isascii() and (character.isalnum() or character in "/-_."))
        if candidate and candidate not in normalized:
            normalized.append(candidate)

    return normalized


def normalize_tag_entries(raw_tags: str | list[str]) -> list[str]:
    """Normalize review failure tags into lower-case underscore-separated values."""
    entries = raw_tags.split(",") if isinstance(raw_tags, str) else raw_tags
    normalized: list[str] = []
    for entry in entries:
        tag = str(entry).strip().lower().replace(" ", "_")
        if tag and tag not in normalized:
            normalized.append(tag)
    return normalized


def parse_simple_yaml_list(path: Path) -> list[str]:
    """Parse simple ``- item`` YAML lists used by the wrapper's config files."""
    items: list[str] = []
    if not path.exists():
        return items

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("- "):
            items.append(line[2:].strip())
    return items


def parse_simple_yaml_mapping(path: Path) -> dict[int, str]:
    """Parse a simple integer-to-string YAML mapping used for score legends."""
    mapping: dict[int, str] = {}
    if not path.exists():
        return mapping

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.endswith(":") or ":" not in line:
            continue
        key, value = line.split(":", maxsplit=1)
        key = key.strip().strip("\"'")
        value = value.strip().strip("\"'")
        if key.isdigit():
            mapping[int(key)] = value
    return mapping


def build_prompt_preview(expected_scope: list[str], rules: list[str]) -> str:
    """Build the starter prompt text written into each new session folder."""
    lines = [
        "Goal: keep aider focused on the requested task and review criteria.",
        "Rules:",
    ]
    lines.extend(f"- {rule}" for rule in rules)
    lines.append("Expected scope:")
    if expected_scope:
        lines.extend(f"- {item}" for item in expected_scope)
    else:
        lines.append("- No explicit scope provided.")
    return "\n".join(lines)


def list_changed_files(repo_path: Path, baseline_ref: str = "") -> list[str]:
    """List changed files from git, optionally relative to a stored baseline ref."""
    command = ["git", "-C", str(repo_path), "diff", "--name-only"]
    if baseline_ref:
        command.append(baseline_ref)

    result = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    return normalize_scope_entries(result.stdout.splitlines())
