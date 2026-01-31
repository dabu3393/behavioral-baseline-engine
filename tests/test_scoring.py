from __future__ import annotations

from datetime import datetime

from baseline_engine.config import BaselineConfig
from baseline_engine.models import BaselineKey, BaselineStats, Event
from baseline_engine.scoring import score_event


def test_score_event_normal() -> None:
    cfg = BaselineConfig(mad_threshold=3.5)

    baseline = BaselineStats(
        key=BaselineKey(entity_id="/login", metric="latency_p95_ms", hour_of_day=14),
        median=100.0,
        mad=10.0,
        sample_count=100,
        training_start=datetime(2026, 1, 1),
        training_end=datetime(2026, 1, 1, 1),
        created_at=datetime(2026, 1, 2),
        version=1,
    )

    event = Event(
        timestamp=datetime(2026, 1, 2, 14, 30),
        entity_id="/login",
        metric="latency_p95_ms",
        value=115.0,
    )

    result = score_event(event, baseline, cfg)

    assert result.is_anomaly is False
    assert result.score == 1.5


def test_score_event_anomalous() -> None:
    cfg = BaselineConfig(mad_threshold=3.5)

    baseline = BaselineStats(
        key=BaselineKey(entity_id="/login", metric="latency_p95_ms", hour_of_day=14),
        median=100.0,
        mad=10.0,
        sample_count=100,
        training_start=datetime(2026, 1, 1),
        training_end=datetime(2026, 1, 1, 1),
        created_at=datetime(2026, 1, 2),
        version=1,
    )

    event = Event(
        timestamp=datetime(2026, 1, 2, 14, 45),
        entity_id="/login",
        metric="latency_p95_ms",
        value=150.0,
    )

    result = score_event(event, baseline, cfg)

    assert result.is_anomaly is True
    assert result.score == 5.0
    assert "MAD above baseline" in result.explanation
