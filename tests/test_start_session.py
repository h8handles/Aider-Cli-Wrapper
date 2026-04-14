import os
import json
from datetime import datetime
from scripts import start_session, review_session, export_diff

import pytest

def test_normalize_task_name():
    assert start_session.normalize_task_name("Test Task") == "test_task"
    assert start_session.normalize_task_name("Task with Spaces") == "task_with_spaces"
    assert start_session.normalize_task_name("Task-With-Dashes") == "task_with_dashes"
    assert start_session.normalize_task_name("Task/With/Slashes") == "task_with_slashes"
    assert start_session.normalize_task_name("Task\\With\\Backslashes") == "task_with_backslashes"
    assert start_session.normalize_task_name("Task with Special Characters!@#") == "task_with_special_characters"

def test_sanitize_expected_scope():
    input_data = "scripts/export_diff.py, script्स/start_session.py, scripts/review_session.py"
    expected_output = ["scripts/export_diff.py", "scripts/start_session.py", "scripts/review_session.py"]
    assert start_session.sanitize_expected_scope(input_data) == expected_output

def test_create_session_folder(tmpdir):
    base_dir = str(tmpdir)
    timestamp = datetime.now().isoformat()
    session_id = f"{timestamp[:10]}_{timestamp[11:13]}{timestamp[14:16]}{timestamp[17:19]}_test_task"
    session_path = start_session.create_session_folder(base_dir, session_id)
    assert os.path.exists(session_path)

def test_write_file(tmpdir):
    file_path = tmpdir.join('test.txt')
    content = "Test Content"
    start_session.write_file(str(file_path), content)
    with open(file_path, 'r') as file:
        assert file.read() == content

def test_main(monkeypatch, template_path, sessions_dir):
    monkeypatch.setattr('os.getcwd', lambda: '/path/to/test_repo')
    monkeypatch.setattr('builtins.input', lambda _: "Test Task")
    monkeypatch.setattr('datetime.datetime.now', lambda: datetime(2023, 10, 1, 12, 34, 56, 789000))

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
        assert session_data['expected_scope'] == []
        assert session_data['failure_tags'] == []
        assert session_data['changed_files'] == []
        assert session_data['verdict'] is None
        assert session_data['score'] is None
        assert session_data['notes_summary'] == ""

    assert os.path.exists(os.path.join(session_path, 'prompt.txt'))
    assert os.path.exists(os.path.join(session_path, 'context_files.txt'))
    assert os.path.exists(os.path.join(session_path, 'notes.txt'))

def test_main_missing_template(monkeypatch):
    monkeypatch.setattr('os.getcwd', lambda: '/path/to/test_repo')
    monkeypatch.setattr('builtins.input', lambda _: "Test Task")
    monkeypatch.setattr('datetime.datetime.now', lambda: datetime(2023, 10, 1, 12, 34, 56, 789000))

    with pytest.raises(SystemExit):
        start_session.main()
