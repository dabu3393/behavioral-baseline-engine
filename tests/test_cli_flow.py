from __future__ import annotations

import json
from pathlib import Path

from baseline_engine.cli import main


def test_cli_train_and_score(tmp_path, capsys) -> None:
    # Create training CSV
    train_csv = tmp_path / "train.csv"
    train_csv.write_text(
        "timestamp,entity_id,metric,value\n"
        "2026-01-01T14:00:00,/login,latency_p95_ms,100\n"
        "2026-01-01T14:01:00,/login,latency_p95_ms,110\n"
        "2026-01-01T14:02:00,/login,latency_p95_ms,90\n",
        encoding="utf-8",
    )

    db_path = tmp_path / "baselines.db"

    # Train with min_samples=3 so it creates a baseline
    rc = main(["train", "--input", str(train_csv), "--db", str(db_path), "--min-samples", "3"])
    assert rc == 0

    # Create scoring CSV
    score_csv = tmp_path / "score.csv"
    score_csv.write_text(
        "timestamp,entity_id,metric,value\n"
        "2026-01-02T14:00:00,/login,latency_p95_ms,150\n",
        encoding="utf-8",
    )

    rc = main(["score", "--input", str(score_csv), "--db", str(db_path), "--min-samples", "3"])
    assert rc == 0

    out = capsys.readouterr().out.strip().splitlines()

    # We should see at least one JSON line output (the AnomalyResult)
    json_line = None
    for line in out:
        if line.startswith("{") and line.endswith("}"):
            json_line = line
            break

    assert json_line is not None
    obj = json.loads(json_line)
    assert obj["event"]["entity_id"] == "/login"
    assert obj["baseline"]["key"]["entity_id"] == "/login"
