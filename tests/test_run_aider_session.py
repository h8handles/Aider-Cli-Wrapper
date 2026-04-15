import json
import subprocess

from scripts import run_aider_session


def test_build_aider_command_uses_session_prompt(session_dir):
    session_data = run_aider_session.load_session_record(session_dir)
    command = run_aider_session.build_aider_command(
        aider_executable="aider",
        config_path=run_aider_session.DEFAULT_CONFIG_PATH,
        session_dir=session_dir,
        session_data=session_data,
        model_override="gpt-4.1",
    )

    assert "--config" in command
    assert "--model" in command
    assert "--message-file" in command
    assert "scripts/export_diff.py" in command


def test_run_session_fails_when_aider_is_missing(monkeypatch, capsys, session_dir):
    session_data = run_aider_session.load_session_record(session_dir)
    monkeypatch.setattr(run_aider_session, "resolve_aider_executable", lambda: None)

    exit_code = run_aider_session.run_session(session_dir, session_data)

    captured = capsys.readouterr()
    assert exit_code == 127
    assert "Could not find the 'aider' executable" in captured.out


def test_run_session_rejects_missing_expected_scope_files(monkeypatch, capsys, session_dir, tmp_path):
    session_data = run_aider_session.load_session_record(session_dir)
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    session_data.repo_path = str(repo_path)

    monkeypatch.setattr(
        run_aider_session,
        "resolve_aider_executable",
        lambda: (_ for _ in ()).throw(AssertionError("aider should not be resolved when scope validation fails")),
    )
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("subprocess.run should not be called when scope validation fails")),
    )

    exit_code = run_aider_session.run_session(session_dir, session_data)

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Expected scope file(s) were not found: scripts/export_diff.py" in captured.out
    assert not (session_dir / "aider_run.json").exists()
    assert not (session_dir / "aider_stdout.txt").exists()
    assert not (session_dir / "aider_stderr.txt").exists()

    session_payload = json.loads((session_dir / "session.json").read_text(encoding="utf-8"))
    assert session_payload["last_run_exit_code"] is None
    assert session_payload["last_run_command"] == []


def test_run_session_saves_artifacts(monkeypatch, session_dir, tmp_path):
    session_data = run_aider_session.load_session_record(session_dir)
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    (repo_path / "scripts").mkdir()
    (repo_path / "scripts" / "export_diff.py").write_text("print('ok')\n", encoding="utf-8")
    session_data.repo_path = str(repo_path)

    monkeypatch.setattr(run_aider_session, "resolve_aider_executable", lambda: "aider")
    monkeypatch.setattr(run_aider_session, "DEFAULT_CONFIG_PATH", tmp_path / ".aider.config.yaml")
    run_aider_session.DEFAULT_CONFIG_PATH.write_text("read:\n  - .aider.rules.md\n", encoding="utf-8")

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(command, returncode=0, stdout="stdout text", stderr="stderr text")

    monkeypatch.setattr(subprocess, "run", fake_run)

    exit_code = run_aider_session.run_session(session_dir, session_data, model_override="gpt-4.1")

    assert exit_code == 0
    assert (session_dir / "aider_stdout.txt").read_text(encoding="utf-8") == "stdout text"
    assert (session_dir / "aider_stderr.txt").read_text(encoding="utf-8") == "stderr text"

    run_payload = json.loads((session_dir / "aider_run.json").read_text(encoding="utf-8"))
    assert run_payload["exit_code"] == 0
    assert "--model" in run_payload["command"]

    session_payload = json.loads((session_dir / "session.json").read_text(encoding="utf-8"))
    assert session_payload["last_run_exit_code"] == 0
    assert session_payload["model_name"] == "gpt-4.1"


def test_run_session_records_oserror_as_failed_run(monkeypatch, capsys, session_dir, tmp_path):
    session_data = run_aider_session.load_session_record(session_dir)
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    (repo_path / "scripts").mkdir()
    (repo_path / "scripts" / "export_diff.py").write_text("print('ok')\n", encoding="utf-8")
    session_data.repo_path = str(repo_path)

    monkeypatch.setattr(run_aider_session, "resolve_aider_executable", lambda: "aider")
    monkeypatch.setattr(run_aider_session, "DEFAULT_CONFIG_PATH", tmp_path / ".aider.config.yaml")
    run_aider_session.DEFAULT_CONFIG_PATH.write_text("read:\n  - .aider.rules.md\n", encoding="utf-8")
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("spawn failed")))

    exit_code = run_aider_session.run_session(session_dir, session_data)

    captured = capsys.readouterr()
    assert exit_code == 127
    assert "Aider run failed with exit code 127" in captured.out
    assert (session_dir / "aider_stdout.txt").read_text(encoding="utf-8") == ""
    assert "spawn failed" in (session_dir / "aider_stderr.txt").read_text(encoding="utf-8")

    run_payload = json.loads((session_dir / "aider_run.json").read_text(encoding="utf-8"))
    assert run_payload["exit_code"] == 127
    assert run_payload["cwd"] == str(repo_path)

    session_payload = json.loads((session_dir / "session.json").read_text(encoding="utf-8"))
    assert session_payload["last_run_exit_code"] == 127
    assert session_payload["last_run_command"]


def test_main_returns_runner_exit_code(monkeypatch, sessions_dir):
    monkeypatch.setattr(run_aider_session, "SESSIONS_DIR", sessions_dir)
    inputs = iter(["1", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr(run_aider_session, "run_session", lambda *args, **kwargs: 5)

    assert run_aider_session.main() == 5
