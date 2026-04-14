import os
import json
from datetime import datetime
import subprocess

import pytest

from scripts import export_diff

def test_load_sessions(tmpdir, session_json):
    sessions_dir = tmpdir.mkdir('sessions')
    os.rename(session_json[0], os.path.join(sessions_dir, 'session_1'))
    loaded_sessions = export_diff.load_sessions(str(sessions_dir))
    assert len(loaded_sessions) == 1
    assert loaded_sessions[0][0] == 'session_1'

def test_display_sessions(capsys):
    sessions = [
        ('session_1', {'task_title': 'Task 1'}),
        ('session_2', {'task_title': 'Task 2'})
    ]
    export_diff.display_sessions(sessions)
    captured = capsys.readouterr()
    assert "1. session_1 - Task 1" in captured.out
    assert "2. session_2 - Task 2" in captured.out

def test_get_user_choice(monkeypatch, tmpdir):
    sessions = [
        ('session_1', {'task_title': 'Task 1'}),
        ('session_2', {'task_title': 'Task 2'})
    ]
    inputs = iter(["2"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    session_id, session_data = export_diff.get_user_choice(sessions)
    assert session_id == 'session_2'
    assert session_data['task_title'] == 'Task 2'

def test_verify_git_repository(monkeypatch):
    repo_path = tmpdir.mkdir('mock_repo')
    (repo_path / '.git').mkdir()
    monkeypatch.setattr(export_diff, "verify_git_repository", lambda x: True)
    assert export_diff.verify_git_repository(str(repo_path))

def test_export_diff(monkeypatch, tmpdir, session_json):
    inputs = iter(["1"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr(export_diff, "load_sessions", lambda x: [('session_1', {'task_title': 'Task 1', 'repo_path': '/path/to/repo'})])
    monkeypatch.setattr('subprocess.run', lambda *args, **kwargs: subprocess.CompletedProcess(args[0], returncode=0, stdout="Diff content"))
    session_path, json_file = session_json
    export_diff.export_diff(session_path, str(tmpdir))
    diff_file = os.path.join(session_path, 'diff.patch')
    assert os.path.exists(diff_file)
    with open(diff_file, 'r') as file:
        assert file.read() == "Diff content"

def test_export_diff_empty(monkeypatch, tmpdir, session_json):
    inputs = iter(["1"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr(export_diff, "load_sessions", lambda x: [('session_1', {'task_title': 'Task 1', 'repo_path': '/path/to/repo'})])
    monkeypatch.setattr('subprocess.run', lambda *args, **kwargs: subprocess.CompletedProcess(args[0], returncode=0, stdout=""))
    session_path, json_file = session_json
    export_diff.export_diff(session_path, str(tmpdir))
    diff_file = os.path.join(session_path, 'diff.patch')
    assert os.path.exists(diff_file)
    with open(diff_file, 'r') as file:
        assert file.read() == ""

def test_main_no_sessions(capsys):
    monkeypatch.setattr(export_diff, "load_sessions", lambda x: [])
    export_diff.main()
    captured = capsys.readouterr()
    assert "No sessions available for diff export." in captured.out

def test_main_invalid_choice(monkeypatch, tmpdir, sessions_dir, datetime_mock):
    inputs = iter(["3", "1"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    with pytest.raises(SystemExit) as exc_info:
        export_diff.main()
    assert exc_info.value.code == 1

def test_main_invalid_score(monkeypatch, tmpdir, sessions_dir, datetime_mock):
    inputs = iter(["1", "invalid"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    with pytest.raises(SystemExit) as exc_info:
        export_diff.main()
    assert exc_info.value.code == 1

def test_main_invalid_failure_tags(monkeypatch, tmpdir, sessions_dir, datetime_mock):
    inputs = iter(["1", "5"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    with pytest.raises(SystemExit) as exc_info:
        export_diff.main()
    assert exc_info.value.code == 1

def test_main_invalid_notes_summary(monkeypatch, tmpdir, sessions_dir, datetime_mock):
    inputs = iter(["1", "5", "invalid"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    with pytest.raises(SystemExit) as exc_info:
        export_diff.main()
    assert exc_info.value.code == 1

def test_main(monkeypatch, tmpdir, sessions_dir, datetime_mock):
    inputs = iter(["Test Task", "general", "scripts/export_diff.py, scriptstartsessionpy, scriptsreviewsessionpy"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    start_session.main()

    session_id = "2023-10-01_123456_test_task"
    session_path = os.path.join(sessions_dir, session_id)
    assert os.path.exists(session_path)

    json_file = os.path.join(session_path, 'session.json')
    with open(json_file, 'r') as file:
        session_data = json.load(file)
        assert session_data['session_id'] == session_id
        assert session_data['timestamp'] == "2023-10-01T12:34:56.789000"
        assert session_data['repo_name'] == "test_repo"
        assert session_data['repo_path'] == "/path/to/test_repo"
        assert session_data['task_title'] == "Test Task"
        assert session_data['task_type'] == "general"
        assert session_data['agent_name'] == "aider"
        assert session_data['model_name'] == ""
        assert session_data['expected_scope'] == ["script/start_session.py"]
        assert session_data['failure_tags'] == []
        assert session_data['changed_files'] == []
        assert session_data['verdict'] is None
        assert session_data['score'] is None
        assert session_data['notes_summary'] == ""

    assert os.path.exists(os.path.join(session_path, 'prompt.txt'))
    assert os.path.exists(os.path.join(session_path, 'context_files.txt'))
    assert os.path.exists(os.path.join(session_path, 'notes.txt'))

def test_main_missing_template(monkeypatch, tmpdir):
    inputs = iter(["Test Task", "general", "scripts/export_diff.py, scriptstartsessionpy, scriptsreviewsessionpy"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    with pytest.raises(SystemExit):
        start_session.main()
