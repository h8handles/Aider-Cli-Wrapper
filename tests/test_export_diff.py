import os
import json

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

def test_get_user_choice(monkeypatch):
    sessions = [
        ('session_1', {'task_title': 'Task 1'}),
        ('session_2', {'task_title': 'Task 2'})
    ]
    monkeypatch.setattr('builtins.input', lambda _: "2")
    session_id, session_data = export_diff.get_user_choice(sessions)
    assert session_id == 'session_2'
    assert session_data['task_title'] == 'Task 2'

def test_verify_git_repository(tmpdir):
    repo_path = tmpdir.mkdir('mock_repo')
    (repo_path / '.git').mkdir()
    assert export_diff.verify_git_repository(str(repo_path))

def test_export_diff(monkeypatch, tmpdir, session_json):
    monkeypatch.setattr('subprocess.run', lambda *args, **kwargs: subprocess.CompletedProcess(args[0], returncode=0, stdout="Diff content"))
    session_path, json_file = session_json
    export_diff.export_diff(session_path, str(tmpdir))
    diff_file = os.path.join(session_path, 'diff.patch')
    assert os.path.exists(diff_file)
    with open(diff_file, 'r') as file:
        assert file.read() == "Diff content"

def test_export_diff_empty(monkeypatch, tmpdir, session_json):
    monkeypatch.setattr('subprocess.run', lambda *args, **kwargs: subprocess.CompletedProcess(args[0], returncode=0, stdout=""))
    session_path, json_file = session_json
    export_diff.export_diff(session_path, str(tmpdir))
    diff_file = os.path.join(session_path, 'diff.patch')
    assert os.path.exists(diff_file)
    with open(diff_file, 'r') as file:
        assert file.read() == ""

def test_main(monkeypatch, sessions_dir, session_json):
    monkeypatch.setattr('os.listdir', lambda _: ['session_1'])
    monkeypatch.setattr('os.path.isdir', lambda x: True)
    monkeypatch.setattr('os.path.exists', lambda x: True)
    monkeypatch.setattr('json.load', lambda x: {'repo_path': '/path/to/repo'})
    monkeypatch.setattr('builtins.input', lambda _: "1")
    monkeypatch.setattr('scripts.export_diff.verify_git_repository', lambda x: True)
    monkeypatch.setattr('scripts.export_diff.export_diff', lambda *args: None)

    export_diff.main()

def test_main_no_sessions(capsys):
    with pytest.raises(SystemExit):
        export_diff.main()
    captured = capsys.readouterr()
    assert "No sessions available for diff export." in captured.out

def test_main_invalid_choice(monkeypatch, sessions_dir, session_json):
    monkeypatch.setattr('os.listdir', lambda _: ['session_1'])
    monkeypatch.setattr('os.path.isdir', lambda x: True)
    monkeypatch.setattr('os.path.exists', lambda x: True)
    monkeypatch.setattr('json.load', lambda x: {'repo_path': '/path/to/repo'})
    monkeypatch.setattr('builtins.input', lambda _: "3")
    with pytest.raises(SystemExit):
        export_diff.main()

def test_main_missing_repo_path(capsys, sessions_dir, session_json):
    monkeypatch.setattr('os.listdir', lambda _: ['session_1'])
    monkeypatch.setattr('os.path.isdir', lambda x: True)
    monkeypatch.setattr('os.path.exists', lambda x: False)
    monkeypatch.setattr('json.load', lambda x: {'repo_path': '/path/to/repo'})
    monkeypatch.setattr('builtins.input', lambda _: "1")
    with pytest.raises(SystemExit):
        export_diff.main()
    captured = capsys.readouterr()
    assert "Error: Repository path /path/to/repo does not exist." in captured.out

def test_main_non_git_repo(capsys, sessions_dir, session_json):
    monkeypatch.setattr('os.listdir', lambda _: ['session_1'])
    monkeypatch.setattr('os.path.isdir', lambda x: True)
    monkeypatch.setattr('os.path.exists', lambda x: True)
    monkeypatch.setattr('json.load', lambda x: {'repo_path': '/path/to/repo'})
    monkeypatch.setattr('builtins.input', lambda _: "1")
    monkeypatch.setattr('scripts.export_diff.verify_git_repository', lambda x: False)
    with pytest.raises(SystemExit):
        export_diff.main()
    captured = capsys.readouterr()
    assert "Error: /path/to/repo is not a valid git repository." in captured.out
