from collections import Counter
from datetime import datetime
from pathlib import Path

from scripts.session_utils import load_sessions as load_session_records, parse_simple_yaml_mapping


ROOT_DIR = Path(__file__).resolve().parent.parent
SESSIONS_DIR = ROOT_DIR / "sessions"
REPORTS_DIR = ROOT_DIR / "reports"
SCORING_PATH = ROOT_DIR / "config" / "scoring.yaml"


def load_sessions(sessions_dir: str | Path):
    return load_session_records(Path(sessions_dir))


def format_average_score(scores: list[int]) -> str:
    return f"{sum(scores) / len(scores):.2f}" if scores else "N/A"


def generate_report(sessions) -> str:
    score_meanings = parse_simple_yaml_mapping(SCORING_PATH)
    session_records = [session for _, session in sessions]
    reviewed_sessions = [session for session in session_records if session.verdict]
    scores = [session.score for session in reviewed_sessions if session.score is not None]
    failure_counts = Counter(tag for session in reviewed_sessions for tag in session.failure_tags)
    low_scoring_sessions = [session for session in reviewed_sessions if session.score is not None and session.score <= 2]
    scope_drift_sessions = [session for session in reviewed_sessions if "scope_drift" in session.failure_tags]

    report = [
        "# Nightly Report",
        "",
        f"Generated on: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Totals",
        f"- Total Sessions: {len(session_records)}",
        f"- Reviewed Sessions: {len(reviewed_sessions)}",
        f"- Unreviewed Sessions: {len(session_records) - len(reviewed_sessions)}",
        f"- Accepted: {sum(1 for session in reviewed_sessions if session.verdict == 'accepted')}",
        f"- Accepted with Edits: {sum(1 for session in reviewed_sessions if session.verdict == 'accepted_with_edits')}",
        f"- Rejected: {sum(1 for session in reviewed_sessions if session.verdict == 'rejected')}",
        "",
        "## Quality Signals",
        f"- Average Score: {format_average_score(scores)}",
        f"- Sessions With Scope Drift: {len(scope_drift_sessions)}",
        f"- Low-Scoring Sessions (<=2): {len(low_scoring_sessions)}",
        "",
        "## Score Legend",
    ]

    if score_meanings:
        report.extend(f"- {score}: {meaning}" for score, meaning in sorted(score_meanings.items(), reverse=True))
    else:
        report.append("- No score legend configured.")

    report.extend(["", "## Top Failure Tags"])
    if not failure_counts:
        report.append("- No failure tags recorded.")
    else:
        report.extend(f"- {tag}: {count}" for tag, count in failure_counts.most_common(5))

    report.extend(["", "## Sessions Needing Attention"])
    if not low_scoring_sessions:
        report.append("- No low-scoring sessions.")
    else:
        for session in sorted(low_scoring_sessions, key=lambda item: (item.score, item.timestamp)):
            # This keeps the report focused on sessions most useful for wrapper tuning.
            report.append(f"- {session.session_id}: score={session.score}, verdict={session.verdict}, tags={', '.join(session.failure_tags) or 'none'}")

    report.extend(
        [
            "",
            "## Per-Session Summary",
            "| Session ID | Task Title | Verdict | Score | Changed Files | Notes Summary |",
            "|------------|------------|---------|-------|---------------|---------------|",
        ]
    )

    for session_id, session in sessions:
        changed_files = ", ".join(session.changed_files) if session.changed_files else "N/A"
        notes_summary = session.notes_summary or "N/A"
        report.append(
            f"| {session_id} | {session.task_title} | {session.verdict or 'unreviewed'} | "
            f"{session.score if session.score is not None else 'N/A'} | {changed_files} | {notes_summary} |"
        )

    return "\n".join(report) + "\n"


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    sessions = load_sessions(SESSIONS_DIR)
    report_content = generate_report(sessions)
    (REPORTS_DIR / "nightly_report.md").write_text(report_content, encoding="utf-8")


if __name__ == "__main__":
    main()
