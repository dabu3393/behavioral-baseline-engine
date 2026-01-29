from __future__ import annotations

from datetime import datetime, timedelta

from baseline_engine.models import BaselineKey, BaselineStats
from baseline_engine.storage_sqlite import BaselineStore


def test_sqlite_store_roundtrip(tmp_path) -> None:
    db_path = tmp_path / "test_baselines.db"
    store = BaselineStore(str(db_path))
    store.init_db()

    base = datetime(2026, 1, 1, 14, 0, 0)

    b = BaselineStats(
        key=BaselineKey(entity_id="/login", metric="latency_p95_ms", hour_of_day=14),
        median=100.0,
        mad=5.0,
        sample_count=50,
        training_start=base,
        training_end=base + timedelta(hours=1),
        created_at=base + timedelta(days=1),
        version=1,
    )

    store.insert_baseline(b)

    rows = store.list_baselines()
    assert len(rows) == 1

    loaded = rows[0]
    assert loaded.key.as_str() == b.key.as_str()
    assert loaded.median == b.median
    assert loaded.mad == b.mad
    assert loaded.sample_count == b.sample_count
    assert loaded.training_start == b.training_start
    assert loaded.training_end == b.training_end
    assert loaded.created_at == b.created_at
    assert loaded.version == b.version


def test_sqlite_store_latest(tmp_path) -> None:
    db_path = tmp_path / "test_baselines.db"
    store = BaselineStore(str(db_path))
    store.init_db()

    base = datetime(2026, 1, 1, 14, 0, 0)
    key = BaselineKey(entity_id="/login", metric="latency_p95_ms", hour_of_day=14)

    b1 = BaselineStats(
        key=key,
        median=100.0,
        mad=5.0,
        sample_count=50,
        training_start=base,
        training_end=base + timedelta(hours=1),
        created_at=base + timedelta(days=1),
        version=1,
    )
    b2 = BaselineStats(
        key=key,
        median=110.0,
        mad=6.0,
        sample_count=60,
        training_start=base,
        training_end=base + timedelta(hours=2),
        created_at=base + timedelta(days=2),
        version=1,
    )

    store.insert_many([b1, b2])

    latest = store.get_latest(key.as_str())
    assert latest is not None
    assert latest.median == 110.0
    assert latest.mad == 6.0
    assert latest.sample_count == 60
