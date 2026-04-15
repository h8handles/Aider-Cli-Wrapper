from scripts import nightly_report


def test_generate_report_includes_quality_sections(sessions_dir, monkeypatch):
    monkeypatch.setattr(nightly_report, "SCORING_PATH", sessions_dir.parent / "scoring.yaml")
    nightly_report.SCORING_PATH.write_text(
        "score_meanings:\n  5: excellent\n  2: weak\n",
        encoding="utf-8",
    )

    sessions = nightly_report.load_sessions(sessions_dir)
    sessions[0][1].verdict = "rejected"
    sessions[0][1].score = 2
    sessions[0][1].failure_tags = ["scope_drift"]
    sessions[0][1].changed_files = ["scripts/export_diff.py"]

    report = nightly_report.generate_report(sessions)

    assert "## Quality Signals" in report
    assert "Sessions With Scope Drift: 1" in report
    assert "## Sessions Needing Attention" in report
    assert "scripts/export_diff.py" in report
