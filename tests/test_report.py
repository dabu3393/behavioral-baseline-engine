from __future__ import annotations

from baseline_engine.cli import main


def test_report_command_writes_markdown(tmp_path) -> None:
    train_out = tmp_path / "train.csv"
    score_out = tmp_path / "score.csv"
    db_path = tmp_path / "baselines.db"
    report_out = tmp_path / "report.md"

    # Generate small demo dataset
    rc = main(
        [
            "demo",
            "--train-out",
            str(train_out),
            "--score-out",
            str(score_out),
            "--start",
            "2026-01-01T00:00:00",
            "--train-days",
            "2",
            "--score-days",
            "1",
            "--interval-minutes",
            "60",
            "--seed",
            "7",
        ]
    )
    assert rc == 0

    # Train
    rc = main(["train", "--input", str(train_out), "--db", str(db_path), "--min-samples", "5"])
    assert rc == 0

    # Report
    rc = main(
        [
            "report",
            "--input",
            str(score_out),
            "--db",
            str(db_path),
            "--out",
            str(report_out),
            "--min-samples",
            "5",
            "--top",
            "5",
        ]
    )
    assert rc == 0
    assert report_out.exists()

    text = report_out.read_text(encoding="utf-8")
    assert "# Baseline Engine Report" in text
    assert "## Coverage" in text
    assert "## Top anomalies" in text
