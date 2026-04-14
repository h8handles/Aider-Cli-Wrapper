import os
import json
from datetime import datetime
from pathlib import Path
import sys
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest

@pytest.fixture
def template_path(tmpdir):
    template_content = {
        "session_id": "",
        "timestamp": "",
        "repo_name": "",
        "repo_path": "",
        "task_title": "",
        "task_type": "",
        "agent_name": "",
        "model_name": "",
        "expected_scope": [],
        "verdict": None,
        "score": None,
        "failure_tags": [],
        "changed_files": [],
        "notes_summary": ""
    }
    template_file = tmpdir.join('session_template.json')
    with open(template_file, 'w') as file:
        json.dump(template_content, file)
    return str(template_file)

@pytest.fixture
def sessions_dir(tmpdir):
    return str(tmpdir.mkdir('sessions'))

@pytest.fixture
def session_data():
    return {
        "session_id": "2023-10-01_123456_test_session",
        "timestamp": "2023-10-01T12:34:56.789Z",
        "repo_name": "test_repo",
        "repo_path": "/path/to/test_repo",
        "task_title": "Test Task",
        "task_type": "general",
        "agent_name": "aider",
        "model_name": "",
        "expected_scope": [],
        "verdict": None,
        "score": None,
        "failure_tags": [],
        "changed_files": [],
        "notes_summary": ""
    }

@pytest.fixture
def session_json(tmpdir, session_data):
    session_path = tmpdir.mkdir('session_1')
    json_file = session_path.join('session.json')
    with open(json_file, 'w') as file:
        json.dump(session_data, file)
    return str(session_path), str(json_file)

@pytest.fixture
def mock_git_repo(tmpdir):
    repo_path = tmpdir.mkdir('mock_repo')
    (repo_path / '.git').mkdir()
    return str(repo_path)

@pytest.fixture
def datetime_mock(monkeypatch):
    class MockDatetime:
        @staticmethod
        def now():
            return datetime(2023, 10, 1, 12, 34, 56, 789000)
    
    monkeypatch.setattr('datetime.datetime', MockDatetime)

@pytest.fixture
def input_mock(monkeypatch):
    inputs = ["Test Task", "general", "scripts/export_diff.py, script्स/start_session.py, scripts/review_session.py"]
    index = 0

    def mock_input(prompt):
        nonlocal index
        if prompt.startswith("Enter the task title"):
            return inputs[index]
        elif prompt.startswith("Enter the task type"):
            return inputs[index + 1]
        elif prompt.startswith("Enter the expected scope as a comma separated list"):
            return inputs[index + 2]
        else:
            raise ValueError(f"Unexpected input prompt: {prompt}")
    
    monkeypatch.setattr('builtins.input', mock_input)
