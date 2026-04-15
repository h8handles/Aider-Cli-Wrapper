import json
import subprocess

from scripts import export_diff


def test_load_sessions(sessions_dir):
    loaded_sessions = export_diff.load_sessions(sessions_dir)
    assert len(loaded_sessions) == 2


def test_display_sessions(capsys, sessions_dir):
    export_diff.display_sessions(export_diff.load_sessions(sessions_dir))
    captured = capsys.readouterr()
    assert "1. session_b - Task for session_b" in captured.out


def test_get_user_choice(monkeypatch, sessions_dir):
    sessions = export_diff.load_sessions(sessions_dir)
    monkeypatch.setattr("builtins.input", lambda _: "2")
    session_id, session_data = export_diff.get_user_choice(sessions)
    assert session_id == "session_a"
    assert session_data.task_title == "Task for session_a"


def test_verify_git_repository(monkeypatch, tmp_path):
    repo_path = tmp_path / "mock_repo"
    repo_path.mkdir()
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], returncode=0, stdout="true"),
    )
    assert export_diff.verify_git_repository(repo_path)


def test_export_diff_updates_session_metadata(monkeypatch, session_dir):
    session_data = export_diff.load_sessions(session_dir.parent)[0][1]
    monkeypatch.setattr(export_diff, "verify_git_commit", lambda repo_path, commit_sha: True)

    def fake_run(command, **kwargs):
        if command[-3:] == ["--stat", "--patch", session_data.baseline_commit_sha]:
            return subprocess.CompletedProcess(command, returncode=0, stdout="diff --git a/file.py b/file.py")
        if command[-2:] == ["--name-only", session_data.baseline_commit_sha]:
            return subprocess.CompletedProcess(command, returncode=0, stdout="file.py\nother.py\n")
        raise AssertionError(f"Unexpected command: {command}")

    monkeypatch.setattr(subprocess, "run", fake_run)
    export_diff.export_diff(session_dir, "repo-path", session_data)

    assert (session_dir / "diff.patch").read_text(encoding="utf-8") == "diff --git a/file.py b/file.py"
    updated_data = json.loads((session_dir / "session.json").read_text(encoding="utf-8"))
    assert updated_data["changed_files"] == ["file.py", "other.py"]


def test_export_diff_empty(monkeypatch, capsys, session_dir):
    session_data = export_diff.load_sessions(session_dir.parent)[0][1]
    monkeypatch.setattr(export_diff, "verify_git_commit", lambda repo_path, commit_sha: True)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], returncode=0, stdout=""),
    )
    export_diff.export_diff(session_dir, "repo-path", session_data)
    captured = capsys.readouterr()
    assert "No changes detected" in captured.out


def test_export_diff_requires_baseline_commit(session_dir):
    session_data = export_diff.load_sessions(session_dir.parent)[0][1]
    session_data.baseline_commit_sha = ""

    try:
        export_diff.export_diff(session_dir, "repo-path", session_data)
    except ValueError as exc:
        assert "missing a baseline commit SHA" in str(exc)
    else:
        raise AssertionError("Expected export_diff() to reject sessions without a baseline commit SHA.")


def test_main_no_sessions(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(export_diff, "SESSIONS_DIR", tmp_path / "sessions")
    (tmp_path / "sessions").mkdir()
    export_diff.main()
    captured = capsys.readouterr()
    assert "No sessions available for diff export." in captured.out


def test_main_exports_selected_session(monkeypatch, capsys, sessions_dir, tmp_path):
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    session_file = sessions_dir / "session_b" / "session.json"
    payload = json.loads(session_file.read_text(encoding="utf-8"))
    payload["repo_path"] = str(repo_path)
    session_file.write_text(json.dumps(payload), encoding="utf-8")

    monkeypatch.setattr("builtins.input", lambda _: "1")
    monkeypatch.setattr(export_diff, "SESSIONS_DIR", sessions_dir)
    monkeypatch.setattr(export_diff, "verify_git_repository", lambda _: True)
    monkeypatch.setattr(export_diff, "export_diff", lambda *args, **kwargs: None)

    export_diff.main()
    captured = capsys.readouterr()
    assert "Diff exported for session session_b successfully." in captured.out
