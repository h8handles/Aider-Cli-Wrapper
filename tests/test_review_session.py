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

def test_get_user_choice(monkeypatch, tmpdir):
    sessions = [
        ('session_1', {'task_title': 'Task 1'}),
        ('session_2', {'task_title': 'Task 2'})
    ]
    inputs = iter(["2"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    session_id, session_data = review_session.get_user_choice(sessions)
    assert session_id == 'session_2'
    assert session_data['task_title'] == 'Task 2'

def test_display_session_details(capsys, tmpdir, session_json):
    sessions_dir = tmpdir.mkdir('sessions')
    os.rename(session_json[0], os.path.join(sessions_dir, 'session_1'))
    session_path, json_file = session_json
    
    # Rename the session folder
    new_session_id = "renamed_session"
    new_session_path = os.path.join(sessions_dir, new_session_id)
    os.rename(os.path.join(sessions_dir, 'session_1'), new_session_path)

    # Recompute the new JSON path inside the renamed folder
    new_json_file = os.path.join(new_session_path, 'session.json')

    with open(new_json_file, 'r') as file:
        session_data = json.load(file)
    
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

def test_get_user_input(monkeypatch, tmpdir):
    inputs = iter(["accepted", "3", "", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    verdict, score, failure_tags, notes_summary = review_session.get_user_input()
    assert verdict == "accepted"
    assert score == 3
    assert failure_tags == []
    assert notes_summary == ""

def test_update_session(monkeypatch, tmpdir, session_json):
    session_path, json_file = session_json
    inputs = iter(["accepted", "5", "", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr(review_session, "load_sessions", lambda x: [('session_1', {'task_title': 'Task 1'})])
    review_session.update_session(session_path, "accepted", 5, [], "")
    with open(json_file, 'r') as file:
        updated_data = json.load(file)
        assert updated_data['verdict'] == "accepted"
        assert updated_data['score'] == 5
        assert updated_data['failure_tags'] == []
        assert updated_data['notes_summary'] == ""

def test_main(monkeypatch, tmpdir, sessions_dir):
    inputs = iter(["1", "accepted", "3", "", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr(review_session, "load_sessions", lambda x: [('session_1', {'session_id': 'session_1', 'task_title': 'Task 1', 'task_type': 'test', 'repo_name': 'aider-learning-lab'})])
    review_session.main()

def test_main_no_sessions(monkeypatch, capsys):
    monkeypatch.setattr(review_session, "load_sessions", lambda x: [])
    review_session.main()
    captured = capsys.readouterr()
    assert "No sessions available for review." in captured.out
    assert captured.err == ""

def test_main_invalid_choice(monkeypatch, tmpdir, sessions_dir):
    inputs = iter(["3", "1"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr(review_session, "load_sessions", lambda x: [('session_1', {'session_id': 'session_1', 'task_title': 'Task 1', 'task_type': 'test', 'repo_name': 'aider-learning-lab'})])
    review_session.main()

def test_main_invalid_score(monkeypatch, tmpdir, sessions_dir):
    inputs = iter(["1", "bad", "3", "", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr(review_session, "load_sessions", lambda x: [('session_1', {'session_id': 'session_1', 'task_title': 'Task 1', 'task_type': 'test', 'repo_name': 'aider-learning-lab'})])
    review_session.main()

def test_main_invalid_failure_tags(monkeypatch, tmpdir, sessions_dir):
    inputs = iter(["1", "accepted", "3", "bad", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr(review_session, "load_sessions", lambda x: [('session_1', {'session_id': 'session_1', 'task_title': 'Task 1', 'task_type': 'test', 'repo_name': 'aider-learning-lab'})])
    review_session.main()

def test_main_invalid_notes_summary(monkeypatch, tmpdir, sessions_dir):
    inputs = iter(["1", "accepted", "3", "", "bad"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr(review_session, "load_sessions", lambda x: [('session_1', {'session_id': 'session_1', 'task_title': 'Task 1', 'task_type': 'test', 'repo_name': 'aider-learning-lab'})])
    review_session.main()
