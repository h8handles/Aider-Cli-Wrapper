import argparse

from scripts import (
    create_and_run_session,
    export_diff,
    nightly_report,
    review_session,
    run_aider_session,
    start_session,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level CLI parser and register wrapper subcommands."""
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Aider wrapper command line tool.",
    )
    subparsers = parser.add_subparsers(dest="command")

    create_parser = subparsers.add_parser("create", help="Create a new session.")
    add_session_creation_arguments(create_parser)

    create_run_parser = subparsers.add_parser("create-run", help="Create a new session and run it with aider.")
    add_session_creation_arguments(create_run_parser)

    run_parser = subparsers.add_parser("run", help="Run an existing session with aider.")
    run_parser.add_argument("--session-id", help="Run a specific session without choosing from the list.")
    run_parser.add_argument("--model", help="Override the stored session model for this run.")

    review_parser = subparsers.add_parser("review", help="Review an existing session.")
    review_parser.add_argument("--session-id", help="Review a specific session without choosing from the list.")

    export_diff_parser = subparsers.add_parser("export-diff", help="Export a diff for an existing session.")
    export_diff_parser.add_argument("--session-id", help="Export a diff for a specific session without choosing from the list.")

    subparsers.add_parser("report", help="Generate the nightly report.")
    return parser


def add_session_creation_arguments(parser: argparse.ArgumentParser) -> None:
    """Attach the common session-creation flags to a subparser."""
    parser.add_argument("--task-title", help="Task title for the new session.")
    parser.add_argument("--task-type", help="Task type for the new session.")
    parser.add_argument("--scope", help="Expected scope as a comma separated list.")
    parser.add_argument("--model", help="Model name for the new session.")


def prompt_with_default(prompt_text: str, default_value: str = "") -> str:
    """Prompt for a value and return the provided input or a supplied default."""
    prompt_suffix = f" [{default_value}]" if default_value else ""
    entered_value = input(f"{prompt_text}{prompt_suffix}: ").strip()
    if entered_value:
        return entered_value
    return default_value


def resolve_session_creation_inputs(args: argparse.Namespace) -> tuple[str, str, str, str]:
    """Resolve session-creation inputs from flags or interactive prompts."""
    if not any([args.task_title, args.task_type, args.scope, args.model]):
        return start_session.prompt_for_session_inputs()

    task_title = args.task_title if args.task_title is not None else prompt_with_default("Enter the task title", "")
    task_type = args.task_type if args.task_type is not None else prompt_with_default(
        "Enter the task type (optional, default is general)",
        "general",
    )
    expected_scope_input = args.scope if args.scope is not None else prompt_with_default(
        "Enter the expected scope as a comma separated list (optional)",
        "",
    )
    model_name = args.model if args.model is not None else prompt_with_default("Enter the model name (optional)", "")
    return task_title, task_type, expected_scope_input, model_name


def normalize_exit_code(result) -> int:
    """Normalize helper return values so command handlers always return an int."""
    if isinstance(result, int):
        return result
    return 0


def find_selected_session(command_name: str, session_id: str | None, sessions):
    """Resolve the target session by explicit id or by prompting from a session list."""
    if session_id:
        for loaded_session_id, session_data in sessions:
            if loaded_session_id == session_id:
                return loaded_session_id, session_data
        print(f"Error: Session '{session_id}' was not found.")
        return None

    if command_name == "run":
        run_aider_session.display_sessions(sessions)
        return run_aider_session.get_user_choice(sessions)
    if command_name == "review":
        review_session.display_sessions(sessions)
        return review_session.get_user_choice(sessions)

    export_diff.display_sessions(sessions)
    return export_diff.get_user_choice(sessions)


def handle_create(args: argparse.Namespace) -> int:
    """Create a new session folder and print a user-facing result message."""
    try:
        task_title, task_type, expected_scope_input, model_name = resolve_session_creation_inputs(args)
        session_path, _ = start_session.create_session(task_title, task_type, expected_scope_input, model_name)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 1
    except FileExistsError as exc:
        print(f"Error: Could not create the session folder: {exc}")
        return 2
    except OSError as exc:
        print(f"Error: Could not create the session: {exc}")
        return 2

    print(f"Session created at: {session_path}")
    return 0


def handle_create_run(args: argparse.Namespace) -> int:
    """Create a session and immediately run aider against that new session."""
    try:
        task_title, task_type, expected_scope_input, model_name = resolve_session_creation_inputs(args)
        session_path, session = start_session.create_session(task_title, task_type, expected_scope_input, model_name)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 1
    except FileExistsError as exc:
        print(f"Error: Could not create the session folder: {exc}")
        return 2
    except OSError as exc:
        print(f"Error: Could not create the session: {exc}")
        return 2

    print(f"Session created at: {session_path}")
    return run_aider_session.run_session(session_path, session)


def handle_run(args: argparse.Namespace) -> int:
    """Run aider for an existing session after validating selection and inputs."""
    if not run_aider_session.SESSIONS_DIR.exists():
        print(f"Error: No sessions directory found at {run_aider_session.SESSIONS_DIR}.")
        return 2

    sessions = run_aider_session.load_sessions(run_aider_session.SESSIONS_DIR)
    if not sessions:
        print("Error: No sessions are available. Create a session first with start_session.py.")
        return 2

    selected_session = find_selected_session("run", args.session_id, sessions)
    if selected_session is None:
        return 2

    session_id, _ = selected_session
    session_dir = run_aider_session.SESSIONS_DIR / session_id
    session_data = run_aider_session.load_session_record(session_dir)
    model_override = args.model if args.model is not None else input(
        "Enter a model override (optional, leave blank to use the stored session model): "
    ).strip()
    return run_aider_session.run_session(session_dir, session_data, model_override=model_override)


def handle_review(args: argparse.Namespace) -> int:
    """Collect review input for a session and persist the updated review fields."""
    if not review_session.SESSIONS_DIR.exists():
        print(f"Error: No sessions directory found at {review_session.SESSIONS_DIR}.")
        return 2

    sessions = review_session.load_sessions(review_session.SESSIONS_DIR)
    if not sessions:
        print("No sessions available for review.")
        return 2

    selected_session = find_selected_session("review", args.session_id, sessions)
    if selected_session is None:
        return 2

    session_id, session_data = selected_session
    review_session.display_session_details(session_data)
    verdict, score, failure_tags, notes_summary = review_session.get_user_input()
    review_session.update_session(review_session.SESSIONS_DIR / session_id, verdict, score, failure_tags, notes_summary)
    print(f"Session {session_id} reviewed and updated successfully.")
    return 0


def handle_export_diff(args: argparse.Namespace) -> int:
    """Export a selected session's diff artifact after validating repo state."""
    if not export_diff.SESSIONS_DIR.exists():
        print(f"Error: No sessions directory found at {export_diff.SESSIONS_DIR}.")
        return 2

    sessions = export_diff.load_sessions(export_diff.SESSIONS_DIR)
    if not sessions:
        print("No sessions available for diff export.")
        return 2

    selected_session = find_selected_session("export-diff", args.session_id, sessions)
    if selected_session is None:
        return 2

    session_id, session_data = selected_session
    repo_path = export_diff.Path(session_data.repo_path)
    if not repo_path.exists():
        print(f"Error: Repository path {repo_path} does not exist.")
        return 2
    if not export_diff.verify_git_repository(repo_path):
        print(f"Error: {repo_path} is not a valid git repository.")
        return 2

    try:
        export_diff.export_diff(export_diff.SESSIONS_DIR / session_id, repo_path, session_data)
    except Exception as exc:
        print(f"Error: Could not export diff: {exc}")
        return 2

    print(f"Diff exported for session {session_id} successfully.")
    return 0


def handle_report(_: argparse.Namespace) -> int:
    """Generate the nightly report and normalize its return value for the CLI."""
    return normalize_exit_code(nightly_report.main())


def run_command(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    """Dispatch parsed CLI arguments to the matching command handler."""
    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "create":
        return handle_create(args)
    if args.command == "create-run":
        return handle_create_run(args)
    if args.command == "run":
        return handle_run(args)
    if args.command == "review":
        return handle_review(args)
    if args.command == "export-diff":
        return handle_export_diff(args)
    if args.command == "report":
        return handle_report(args)

    print(f"Error: Unsupported command '{args.command}'.")
    return 2


def main(argv: list[str] | None = None) -> int:
    """Parse CLI arguments, run the selected command, and map interrupts to exit codes."""
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        return run_command(args, parser)
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        return 130
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 1


if __name__ == "__main__":
    raise SystemExit(main())
