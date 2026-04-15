from scripts import create_and_run_session


def test_main_creates_session_and_runs_aider(monkeypatch, tmp_path):
    created_session_path = tmp_path / "sessions" / "session_1"
    created_session = object()

    monkeypatch.setattr(
        create_and_run_session,
        "prompt_for_session_inputs",
        lambda: ("Test Task", "general", "scripts/export_diff.py", "gpt-4.1"),
    )
    monkeypatch.setattr(
        create_and_run_session,
        "create_session",
        lambda *args, **kwargs: (created_session_path, created_session),
    )
    monkeypatch.setattr(
        create_and_run_session,
        "run_session",
        lambda session_path, session: 7 if session_path == created_session_path and session is created_session else 1,
    )

    assert create_and_run_session.main() == 7


def test_main_returns_creation_failure(monkeypatch):
    monkeypatch.setattr(
        create_and_run_session,
        "prompt_for_session_inputs",
        lambda: ("Test Task", "general", "", ""),
    )
    monkeypatch.setattr(
        create_and_run_session,
        "create_session",
        lambda *args, **kwargs: (_ for _ in ()).throw(SystemExit(1)),
    )

    assert create_and_run_session.main() == 1
