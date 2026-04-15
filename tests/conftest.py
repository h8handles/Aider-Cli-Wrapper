import json
import sys
from pathlib import Path

import pytest


ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


@pytest.fixture
def session_payload():
    return {
        "session_id": "2023-10-01_123456_test_session",
        "timestamp": "2023-10-01T12:34:56",
        "repo_name": "test_repo",
        "repo_path": str(ROOT_DIR),
        "task_title": "Test Task",
        "task_type": "general",
        "agent_name": "aider",
        "model_name": "",
        "expected_scope": ["scripts/export_diff.py"],
        "verdict": None,
        "score": None,
        "failure_tags": [],
        "changed_files": [],
        "notes_summary": "",
        "prompt_preview": "Goal: keep aider focused on the requested task and review criteria.",
        "last_run_command": [],
        "last_run_exit_code": None,
        "last_run_started_at": "",
        "last_run_finished_at": "",
        "last_run_duration_seconds": None,
    }


@pytest.fixture
def session_dir(tmp_path, session_payload):
    target = tmp_path / "session_1"
    target.mkdir()
    (target / "session.json").write_text(json.dumps(session_payload), encoding="utf-8")
    (target / "prompt.txt").write_text("Fix the selected file.", encoding="utf-8")
    return target


@pytest.fixture
def sessions_dir(tmp_path, session_payload):
    target = tmp_path / "sessions"
    target.mkdir()
    for name in ("session_a", "session_b"):
        session_dir = target / name
        session_dir.mkdir()
        payload = dict(session_payload)
        payload["session_id"] = name
        payload["task_title"] = f"Task for {name}"
        (session_dir / "session.json").write_text(json.dumps(payload), encoding="utf-8")
        (session_dir / "prompt.txt").write_text(f"Prompt for {name}", encoding="utf-8")
    return target
