from __future__ import annotations

from baseline_engine.cli import main


def test_cli_keys_list_show(tmp_path, capsys) -> None:
    train_csv = tmp_path / "train.csv"
    train_csv.write_text(
        "timestamp,entity_id,metric,value\n"
        "2026-01-01T14:00:00,/login,latency_p95_ms,100\n"
        "2026-01-01T14:01:00,/login,latency_p95_ms,110\n"
        "2026-01-01T14:02:00,/login,latency_p95_ms,90\n",
        encoding="utf-8",
    )

    db_path = tmp_path / "baselines.db"
    rc = main(["train", "--input", str(train_csv), "--db", str(db_path), "--min-samples", "3"])
    assert rc == 0

    # keys
    rc = main(["keys", "--db", str(db_path)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "/login:latency_p95_ms:hour=14" in out

    # list
    rc = main(["list", "--db", str(db_path)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "/login:latency_p95_ms:hour=14" in out

    # show
    rc = main(["show", "--db", str(db_path), "--key", "/login:latency_p95_ms:hour=14"])
    assert rc == 0
    out = capsys.readouterr().out
    assert '"median"' in out
    assert '"mad"' in out
