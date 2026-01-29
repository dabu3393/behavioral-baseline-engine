from __future__ import annotations

from datetime import datetime, timedelta

from baseline_engine.baseline import compute_median_and_mad, train_baselines
from baseline_engine.config import BaselineConfig
from baseline_engine.models import Event


def test_compute_median_and_mad_basic() -> None:
    values = [10, 10, 10, 10, 50]
    med, mad = compute_median_and_mad(values, min_mad=1e-6)
    assert med == 10.0
    # abs devs = [0,0,0,0,40] => median is 0, but we clamp to min_mad
    assert mad == 1e-6


def test_train_baselines_respects_min_samples() -> None:
    cfg = BaselineConfig(use_hour_of_day=True, min_samples=5, mad_threshold=3.5, min_mad=1e-6)

    base = datetime(2026, 1, 1, 14, 0, 0)
    events = [
        Event(timestamp=base + timedelta(minutes=i), entity_id="/login", metric="latency_p95_ms", value=100.0)
        for i in range(4)  # only 4 events, below min_samples
    ]

    baselines = train_baselines(events, cfg)
    assert baselines == []


def test_train_baselines_creates_baseline_per_hour_bucket() -> None:
    cfg = BaselineConfig(use_hour_of_day=True, min_samples=3, mad_threshold=3.5, min_mad=1e-6)

    base = datetime(2026, 1, 1, 14, 0, 0)
    events = [
        Event(timestamp=base + timedelta(minutes=0), entity_id="/login", metric="latency_p95_ms", value=100.0),
        Event(timestamp=base + timedelta(minutes=1), entity_id="/login", metric="latency_p95_ms", value=110.0),
        Event(timestamp=base + timedelta(minutes=2), entity_id="/login", metric="latency_p95_ms", value=90.0),

        # Next hour (15:xx) should become a separate baseline
        Event(timestamp=base + timedelta(hours=1, minutes=0), entity_id="/login", metric="latency_p95_ms", value=200.0),
        Event(timestamp=base + timedelta(hours=1, minutes=1), entity_id="/login", metric="latency_p95_ms", value=210.0),
        Event(timestamp=base + timedelta(hours=1, minutes=2), entity_id="/login", metric="latency_p95_ms", value=190.0),
    ]

    baselines = train_baselines(events, cfg)
    assert len(baselines) == 2

    keys = sorted([b.key.as_str() for b in baselines])
    assert keys == ["/login:latency_p95_ms:hour=14", "/login:latency_p95_ms:hour=15"]
