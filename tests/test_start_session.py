import json
from pathlib import Path

import pytest

from scripts import start_session


def test_normalize_task_name():
    assert start_session.normalize_task_name("Test Task") == "test_task"
    assert start_session.normalize_task_name("Task/With/Slashes") == "task_with_slashes"
    assert start_session.normalize_task_name("!!!") == "task"


def test_sanitize_expected_scope():
    input_data = r"scripts\export_diff.py, scripts/review_session.py, scripts/export_diff.py"
    assert start_session.sanitize_expected_scope(input_data) == [
        "scripts/export_diff.py",
        "scripts/review_session.py",
    ]


def test_create_session_folder(tmp_path):
    session_path = start_session.create_session_folder(tmp_path, "2026-04-14_120000_test_task")
    assert Path(session_path).exists()


def test_write_file(tmp_path):
    file_path = tmp_path / "test.txt"
    start_session.write_file(file_path, "Test Content")
    assert file_path.read_text(encoding="utf-8") == "Test Content"


def test_load_template_missing_file(tmp_path):
    with pytest.raises(SystemExit):
        start_session.load_template(tmp_path / "missing.json")


def test_build_session_record_includes_prompt_preview(monkeypatch):
    monkeypatch.setattr(start_session, "load_rules", lambda: ["preserve imports", "prefer scoped changes"])
    session = start_session.build_session_record(
        task_title="Fix diff export",
        task_type="bugfix",
        expected_scope=["scripts/export_diff.py"],
        model_name="gpt-4.1",
    )

    assert session.repo_name == Path(start_session.ROOT_DIR).name
    assert "preserve imports" in session.prompt_preview
    assert "scripts/export_diff.py" in session.prompt_preview


def test_create_session_creates_session_files(tmp_path, monkeypatch):
    template_path = tmp_path / "session_template.json"
    template_path.write_text(json.dumps({"session_id": ""}), encoding="utf-8")

    monkeypatch.setattr(start_session, "TEMPLATE_PATH", template_path)
    monkeypatch.setattr(start_session, "SESSIONS_DIR", tmp_path / "sessions")
    monkeypatch.setattr(start_session, "load_rules", lambda: ["prefer scoped changes"])

    session_dir, session = start_session.create_session(
        "Test Task",
        "general",
        "scripts/export_diff.py, scripts/review_session.py",
        "gpt-4.1",
    )

    assert session.task_title == "Test Task"
    session_json = json.loads((session_dir / "session.json").read_text(encoding="utf-8"))
    assert session_json["task_title"] == "Test Task"
    assert session_json["expected_scope"] == ["scripts/export_diff.py", "scripts/review_session.py"]


def test_main_creates_session_files(tmp_path, monkeypatch):
    template_path = tmp_path / "session_template.json"
    template_path.write_text(json.dumps({"session_id": ""}), encoding="utf-8")

    inputs = iter(["Test Task", "general", "scripts/export_diff.py, scripts/review_session.py", "gpt-4.1"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr(start_session, "TEMPLATE_PATH", template_path)
    monkeypatch.setattr(start_session, "SESSIONS_DIR", tmp_path / "sessions")
    monkeypatch.setattr(start_session, "load_rules", lambda: ["prefer scoped changes"])

    start_session.main()

    created_sessions = list((tmp_path / "sessions").iterdir())
    assert len(created_sessions) == 1
    session_dir = created_sessions[0]

    session_json = json.loads((session_dir / "session.json").read_text(encoding="utf-8"))
    assert session_json["task_title"] == "Test Task"
    assert session_json["expected_scope"] == ["scripts/export_diff.py", "scripts/review_session.py"]
    assert "prefer scoped changes" in (session_dir / "prompt.txt").read_text(encoding="utf-8")
