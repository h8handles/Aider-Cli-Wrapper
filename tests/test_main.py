import json

import main
from scripts.session_utils import read_json


def test_build_parser_includes_expected_subcommands():
    parser = main.build_parser()
    help_text = parser.format_help()

    assert "create" in help_text
    assert "create-run" in help_text
    assert "export-diff" in help_text
    assert "report" in help_text


def test_main_without_arguments_shows_help(capsys):
    assert main.main([]) == 0

    captured = capsys.readouterr()
    assert "usage:" in captured.out
    assert "Aider wrapper command line tool." in captured.out


def test_resolve_session_creation_inputs_uses_existing_prompt_when_flags_are_missing(monkeypatch):
    parser = main.build_parser()
    args = parser.parse_args(["create"])

    monkeypatch.setattr(
        main.start_session,
        "prompt_for_session_inputs",
        lambda: ("Task", "general", "scripts/export_diff.py", "gpt-4.1"),
    )

    assert main.resolve_session_creation_inputs(args) == (
        "Task",
        "general",
        "scripts/export_diff.py",
        "gpt-4.1",
    )


def test_handle_create_uses_optional_flags_without_prompting(monkeypatch, tmp_path):
    parser = main.build_parser()
    args = parser.parse_args(
        [
            "create",
            "--task-title",
            "Test Task",
            "--task-type",
            "general",
            "--scope",
            "scripts/export_diff.py",
            "--model",
            "gpt-4.1",
        ]
    )

    captured_calls = []
    monkeypatch.setattr(main, "prompt_with_default", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("prompt should not run")))
    monkeypatch.setattr(
        main.start_session,
        "create_session",
        lambda task_title, task_type, scope, model: captured_calls.append((task_title, task_type, scope, model)) or (tmp_path / "session_1", object()),
    )

    assert main.handle_create(args) == 0
    assert captured_calls == [("Test Task", "general", "scripts/export_diff.py", "gpt-4.1")]


def test_handle_create_run_reuses_existing_runner(monkeypatch, tmp_path):
    parser = main.build_parser()
    args = parser.parse_args(["create-run", "--task-title", "Test Task"])

    monkeypatch.setattr(
        main,
        "prompt_with_default",
        lambda prompt_text, default_value="": {
            "Enter the task title": "Test Task",
            "Enter the task type (optional, default is general)": "general",
            "Enter the expected scope as a comma separated list (optional)": "",
            "Enter the model name (optional)": "",
        }[prompt_text],
    )

    session = object()
    monkeypatch.setattr(main.start_session, "create_session", lambda *args, **kwargs: (tmp_path / "session_2", session))
    monkeypatch.setattr(main.run_aider_session, "run_session", lambda session_path, session_data: 9 if session_data is session else 1)

    assert main.handle_create_run(args) == 9


def test_handle_run_uses_session_id_and_model_flag(monkeypatch, sessions_dir):
    parser = main.build_parser()
    args = parser.parse_args(["run", "--session-id", "session_b", "--model", "gpt-4.1"])

    monkeypatch.setattr(main.run_aider_session, "SESSIONS_DIR", sessions_dir)
    captured_calls = []
    monkeypatch.setattr(
        main.run_aider_session,
        "run_session",
        lambda session_dir, session_data, model_override="": captured_calls.append((session_dir.name, session_data.task_title, model_override)) or 5,
    )

    assert main.handle_run(args) == 5
    assert captured_calls == [("session_b", "Task for session_b", "gpt-4.1")]


def test_handle_review_uses_selected_session_id(monkeypatch, sessions_dir):
    parser = main.build_parser()
    args = parser.parse_args(["review", "--session-id", "session_a"])

    monkeypatch.setattr(main.review_session, "SESSIONS_DIR", sessions_dir)
    monkeypatch.setattr(main.review_session, "display_session_details", lambda session_data: None)
    monkeypatch.setattr(main.review_session, "get_user_input", lambda: ("accepted", 4, ["scope_drift"], "Looks good"))
    updated_sessions = []
    monkeypatch.setattr(
        main.review_session,
        "update_session",
        lambda session_path, verdict, score, failure_tags, notes_summary: updated_sessions.append(
            (session_path.name, verdict, score, failure_tags, notes_summary)
        ),
    )

    assert main.handle_review(args) == 0
    assert updated_sessions == [("session_a", "accepted", 4, ["scope_drift"], "Looks good")]


def test_handle_export_diff_uses_selected_session_id(monkeypatch, sessions_dir, tmp_path):
    parser = main.build_parser()
    args = parser.parse_args(["export-diff", "--session-id", "session_b"])

    session_file = sessions_dir / "session_b" / "session.json"
    payload = read_json(session_file)
    payload["repo_path"] = str(tmp_path)
    session_file.write_text(json.dumps(payload), encoding="utf-8")

    monkeypatch.setattr(main.export_diff, "SESSIONS_DIR", sessions_dir)
    monkeypatch.setattr(main.export_diff, "verify_git_repository", lambda _: True)
    exported = []
    monkeypatch.setattr(
        main.export_diff,
        "export_diff",
        lambda session_path, repo_path, session_data=None: exported.append((session_path.name, str(repo_path), session_data.task_title)),
    )

    assert main.handle_export_diff(args) == 0
    assert exported == [("session_b", str(tmp_path), "Task for session_b")]


def test_main_routes_report_subcommand(monkeypatch):
    calls = []
    monkeypatch.setattr(main.nightly_report, "main", lambda: calls.append("report"))

    assert main.main(["report"]) == 0
    assert calls == ["report"]


def test_handle_run_returns_error_for_missing_session_id(monkeypatch, capsys, sessions_dir):
    parser = main.build_parser()
    args = parser.parse_args(["run", "--session-id", "missing"])

    monkeypatch.setattr(main.run_aider_session, "SESSIONS_DIR", sessions_dir)

    assert main.handle_run(args) == 2

    captured = capsys.readouterr()
    assert "Error: Session 'missing' was not found." in captured.out


def test_main_returns_keyboard_interrupt_exit_code(monkeypatch, capsys):
    monkeypatch.setattr(main, "run_command", lambda args, parser: (_ for _ in ()).throw(KeyboardInterrupt))

    assert main.main(["report"]) == 130

    captured = capsys.readouterr()
    assert "Operation cancelled." in captured.out
