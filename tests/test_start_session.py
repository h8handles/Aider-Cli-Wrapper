import os
import json
from datetime import datetime

import pytest

from scripts import start_session

def test_normalize_task_name():
    assert start_session.normalize_task_name("Test Task") == "test_task"
    assert start_session.normalize_task_name("Task with Spaces") == "task_with_spaces"
    assert start_session.normalize_task_name("Task-With-Dashes") == "task_with_dashes"
    assert start_session.normalize_task_name("Task/With/Slashes") == "task_with_slashes"
    assert start_session.normalize_task_name("Task\\With\\Backslashes") == "task_with_backslashes"
    assert start_session.normalize_task_name("Task with Special Characters!@#") == "task_with_special_characters___"

def test_sanitize_expected_scope():
    input_data = "scripts/export_diff.py, scriptstartsessionpy, scriptsreviewsessionpy"
    expected_output = ["script/start_session.py", "script/review_session.py"]
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

def test_main(monkeypatch, tmpdir, sessions_dir, datetime_mock):
    inputs = iter([
        "Test Task",
        "general",
        "scripts/export_diff.py, scriptstartsessionpy, scriptsreviewsessionpy",
        ""
    ])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    start_session.main()

    # Assert that the sessions directory exists
    assert os.path.exists(sessions_dir)

    # Assert that at least one session folder was created
    session_folders = [f for f in os.listdir(sessions_dir) if os.path.isdir(os.path.join(sessions_dir, f))]
    assert len(session_folders) > 0

    # Assert that the created session folder contains session.json
    for session_folder in session_folders:
        session_path = os.path.join(sessions_dir, session_folder)
        json_file = os.path.join(session_path, 'session.json')
        assert os.path.exists(json_file)

def test_main_missing_template(monkeypatch, tmpdir):
    inputs = iter([
        "Test Task",
        "general",
        "scripts/export_diff.py, scriptstartsessionpy, scriptsreviewsessionpy",
        ""
    ])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    with pytest.raises(SystemExit):
        start_session.main()
