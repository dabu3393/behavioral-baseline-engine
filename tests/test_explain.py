from __future__ import annotations

from baseline_engine.cli import main


def test_explain_command(tmp_path, capsys) -> None:
    train_out = tmp_path / "train.csv"
    score_out = tmp_path / "score.csv"
    db_path = tmp_path / "baselines.db"

    # Generate demo data
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
            "11",
        ]
    )
    assert rc == 0

    # Train baselines
    rc = main(["train", "--input", str(train_out), "--db", str(db_path), "--min-samples", "2"])
    assert rc == 0

    # Pick a known timestamp row from score window start (train_days=2 => score starts 2026-01-03T00:00:00)
    rc = main(
        [
            "explain",
            "--input",
            str(score_out),
            "--db",
            str(db_path),
            "--timestamp",
            "2026-01-03T00:00:00",
            "--entity",
            "/login",
            "--metric",
            "latency_p95_ms",
            "--min-samples",
            "2",
        ]
    )
    assert rc == 0

    out = capsys.readouterr().out
    assert "Derived key:" in out
    assert "Baseline:" in out
    assert "Score:" in out
