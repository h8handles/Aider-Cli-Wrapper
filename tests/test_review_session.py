import os
import json

import pytest

from scripts import review_session

def test_load_sessions(tmpdir, session_json):
    sessions_dir = tmpdir.mkdir('sessions')
    os.rename(session_json[0], os.path.join(sessions_dir, 'session_1'))
    loaded_sessions = review_session.load_sessions(str(sessions_dir))
    assert len(loaded_sessions) == 1
    assert loaded_sessions[0][0] == 'session_1'

def test_display_sessions(capsys):
    sessions = [
        ('session_1', {'task_title': 'Task 1'}),
        ('session_2', {'task_title': 'Task 2'})
    ]
    review_session.display_sessions(sessions)
    captured = capsys.readouterr()
    assert "1. session_1 - Task 1" in captured.out
    assert "2. session_2 - Task 2" in captured.out

def test_get_user_choice(monkeypatch):
    sessions = [
        ('session_1', {'task_title': 'Task 1'}),
        ('session_2', {'task_title': 'Task 2'})
    ]
    monkeypatch.setattr('builtins.input', lambda _: "2")
    session_id, session_data = review_session.get_user_choice(sessions)
    assert session_id == 'session_2'
    assert session_data['task_title'] == 'Task 2'

def test_display_session_details(capsys, session_data):
    review_session.display_session_details(session_data)
    captured = capsys.readouterr()
    assert "Session ID: 2023-10-01_123456_test_session" in captured.out
    assert "Task Title: Test Task" in captured.out
    assert "Task Type: general" in captured.out
    assert "Repo Name: test_repo" in captured.out
    assert "Expected Scope: N/A" in captured.out
    assert "Current Verdict: None" in captured.out
    assert "Current Score: None" in captured.out
    assert "Current Failure Tags: N/A" in captured.out
    assert "Current Notes Summary: N/A" in captured.out

def test_get_user_input(monkeypatch):
    monkeypatch.setattr('builtins.input', lambda _: "accepted")
    verdict, score, failure_tags, notes_summary = review_session.get_user_input()
    assert verdict == "accepted"
    assert score == 0
    assert failure_tags == []
    assert notes_summary == ""

def test_update_session(tmpdir, session_json):
    session_path, json_file = session_json
    review_session.update_session(session_path, "accepted", 5, ["tag1"], "Summary")
    with open(json_file, 'r') as file:
        updated_data = json.load(file)
        assert updated_data['verdict'] == "accepted"
        assert updated_data['score'] == 5
        assert updated_data['failure_tags'] == ["tag1"]
        assert updated_data['notes_summary'] == "Summary"

def test_main(monkeypatch, sessions_dir, session_json):
    monkeypatch.setattr('os.listdir', lambda _: ['session_1'])
    monkeypatch.setattr('os.path.isdir', lambda x: True)
    monkeypatch.setattr('os.path.exists', lambda x: True)
    monkeypatch.setattr('json.load', lambda x: {'task_title': 'Test Task'})
    monkeypatch.setattr('builtins.input', lambda _: "1")
    monkeypatch.setattr('scripts.review_session.display_session_details', lambda x: None)
    monkeypatch.setattr('scripts.review_session.get_user_input', lambda: ("accepted", 5, ["tag1"], "Summary"))
    monkeypatch.setattr('scripts.review_session.update_session', lambda *args: None)

    review_session.main()

def test_main_no_sessions(capsys):
    with pytest.raises(SystemExit):
        review_session.main()
    captured = capsys.readouterr()
    assert "No sessions available for review." in captured.out

def test_main_invalid_choice(monkeypatch, sessions_dir, session_json):
    monkeypatch.setattr('os.listdir', lambda _: ['session_1'])
    monkeypatch.setattr('os.path.isdir', lambda x: True)
    monkeypatch.setattr('os.path.exists', lambda x: True)
    monkeypatch.setattr('json.load', lambda x: {'task_title': 'Test Task'})
    monkeypatch.setattr('builtins.input', lambda _: "3")
    with pytest.raises(SystemExit):
        review_session.main()
