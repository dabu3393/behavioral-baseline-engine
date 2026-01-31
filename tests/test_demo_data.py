from __future__ import annotations

from pathlib import Path

from baseline_engine.cli import main


def test_demo_command_creates_files(tmp_path) -> None:
    train_out = tmp_path / "train.csv"
    score_out = tmp_path / "score.csv"

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
            "1",
            "--score-days",
            "1",
            "--interval-minutes",
            "60",
            "--seed",
            "1",
        ]
    )
    assert rc == 0
    assert train_out.exists()
    assert score_out.exists()

    # Basic header sanity
    train_text = train_out.read_text(encoding="utf-8").splitlines()
    score_text = score_out.read_text(encoding="utf-8").splitlines()
    assert train_text[0] == "timestamp,entity_id,metric,value"
    assert score_text[0] == "timestamp,entity_id,metric,value"
