import json

from scripts import review_session


def test_load_sessions(sessions_dir):
    loaded_sessions = review_session.load_sessions(sessions_dir)
    assert [session_id for session_id, _ in loaded_sessions] == ["session_b", "session_a"]


def test_display_sessions(capsys, sessions_dir):
    review_session.display_sessions(review_session.load_sessions(sessions_dir))
    captured = capsys.readouterr()
    assert "1. session_b - Task for session_b" in captured.out
    assert "2. session_a - Task for session_a" in captured.out


def test_get_user_choice(monkeypatch, sessions_dir):
    sessions = review_session.load_sessions(sessions_dir)
    monkeypatch.setattr("builtins.input", lambda _: "2")
    session_id, session_data = review_session.get_user_choice(sessions)
    assert session_id == "session_a"
    assert session_data.task_title == "Task for session_a"


def test_display_session_details(capsys, session_dir):
    session_data = review_session.load_sessions(session_dir.parent)[0][1]
    review_session.display_session_details(session_data)
    captured = capsys.readouterr()
    assert "Session ID: 2023-10-01_123456_test_session" in captured.out
    assert "Changed Files: N/A" in captured.out


def test_prompt_for_failure_tags_retries_invalid(monkeypatch):
    inputs = iter(["bad_tag", "scope_drift, partial_fix_only"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr(review_session, "load_allowed_failure_tags", lambda: {"scope_drift", "partial_fix_only"})

    assert review_session.prompt_for_failure_tags() == ["scope_drift", "partial_fix_only"]


def test_get_user_input(monkeypatch):
    inputs = iter(["accepted", "3", "scope_drift", "Needs tighter file scoping"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr(review_session, "load_allowed_failure_tags", lambda: {"scope_drift"})

    verdict, score, failure_tags, notes_summary = review_session.get_user_input()
    assert (verdict, score, failure_tags, notes_summary) == (
        "accepted",
        3,
        ["scope_drift"],
        "Needs tighter file scoping",
    )


def test_update_session(session_dir):
    review_session.update_session(session_dir, "accepted", 5, ["scope_drift"], "Reviewed")
    updated_data = json.loads((session_dir / "session.json").read_text(encoding="utf-8"))
    assert updated_data["verdict"] == "accepted"
    assert updated_data["score"] == 5
    assert updated_data["failure_tags"] == ["scope_drift"]
    assert updated_data["notes_summary"] == "Reviewed"


def test_main_no_sessions(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(review_session, "SESSIONS_DIR", tmp_path / "missing")
    review_session.main()
    captured = capsys.readouterr()
    assert "Error: No sessions directory found" in captured.out


def test_main_updates_selected_session(monkeypatch, capsys, sessions_dir):
    inputs = iter(["1", "accepted_with_edits", "4", "", "Looks good"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr(review_session, "SESSIONS_DIR", sessions_dir)
    monkeypatch.setattr(review_session, "load_allowed_failure_tags", lambda: {"scope_drift"})

    review_session.main()

    captured = capsys.readouterr()
    assert "reviewed and updated successfully" in captured.out
    updated_data = json.loads((sessions_dir / "session_b" / "session.json").read_text(encoding="utf-8"))
    assert updated_data["verdict"] == "accepted_with_edits"
    assert updated_data["score"] == 4
