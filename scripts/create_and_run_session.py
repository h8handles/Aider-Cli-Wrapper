from scripts.run_aider_session import run_session
from scripts.start_session import create_session, prompt_for_session_inputs


def main() -> int:
    try:
        task_title, task_type, expected_scope_input, model_name = prompt_for_session_inputs()
        session_path, session = create_session(task_title, task_type, expected_scope_input, model_name)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 1
    except FileExistsError as exc:
        print(f"Error: Could not create the session folder: {exc}")
        return 2
    except OSError as exc:
        print(f"Error: Could not create the session: {exc}")
        return 2

    print(f"Session created at: {session_path}")
    return run_session(session_path, session)


if __name__ == "__main__":
    raise SystemExit(main())
