from __future__ import annotations

import csv
import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional


@dataclass(frozen=True)
class DemoConfig:
    # Time range
    start: datetime
    train_days: int = 7
    score_days: int = 2
    interval_minutes: int = 5

    # Entities + metric
    endpoints: tuple[str, ...] = ("/login", "/search", "/checkout")
    metric: str = "latency_p95_ms"

    # Latency behavior (ms)
    base_latency_by_endpoint: Dict[str, float] = None  # filled in __post_init__-ish behavior below
    daily_amplitude_ms: float = 35.0  # seasonality amplitude
    noise_std_ms: float = 8.0         # random noise

    # Incident (applied during score window only)
    incident_enabled: bool = True
    incident_day_offset: int = 0  # 0 = first day of score window
    incident_start_hour: int = 13
    incident_duration_hours: int = 4
    incident_endpoints: tuple[str, ...] = ("/login", "/checkout")
    incident_multiplier: float = 1.8  # sustained degradation multiplier
    incident_spike_ms: float = 120.0  # sharp spike at incident start

    # Reproducibility
    seed: int = 42


def _default_base_latency(endpoints: Iterable[str]) -> Dict[str, float]:
    # Reasonable p95-ish baseline differences by endpoint.
    base = {}
    for ep in endpoints:
        if ep == "/login":
            base[ep] = 95.0
        elif ep == "/search":
            base[ep] = 120.0
        elif ep == "/checkout":
            base[ep] = 140.0
        else:
            base[ep] = 110.0
    return base


def _daily_seasonality(hour: int, amplitude: float) -> float:
    """
    Smooth daily pattern using a sine wave.
    Peak around mid-day, trough overnight.
    Returns an additive delta in ms.
    """
    # Map hour (0..23) to radians. Shift so peak near 14:00.
    radians = (2 * math.pi) * (hour / 24.0)
    shift = -2.0  # shifts the peak later in the day
    return amplitude * math.sin(radians + shift)


def _is_in_incident_window(ts: datetime, cfg: DemoConfig, score_start: datetime) -> bool:
    if not cfg.incident_enabled:
        return False

    incident_day = score_start.date() + timedelta(days=cfg.incident_day_offset)
    if ts.date() != incident_day:
        return False

    start = datetime(ts.year, ts.month, ts.day, cfg.incident_start_hour, 0, 0)
    end = start + timedelta(hours=cfg.incident_duration_hours)
    return start <= ts < end


def generate_events_csv(
    out_path: str,
    *,
    cfg: DemoConfig,
    window_start: datetime,
    days: int,
    apply_incident: bool,
) -> None:
    """
    Generate a CSV of events with columns:
      timestamp,entity_id,metric,value

    entity_id is the endpoint.
    metric is cfg.metric.
    """
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    rng = random.Random(cfg.seed)

    base_latency = cfg.base_latency_by_endpoint or _default_base_latency(cfg.endpoints)

    # For incident timing we need the score window start (even when generating train window)
    score_start = cfg.start + timedelta(days=cfg.train_days)

    rows: List[dict] = []
    ts = window_start
    end = window_start + timedelta(days=days)

    step = timedelta(minutes=cfg.interval_minutes)

    while ts < end:
        for ep in cfg.endpoints:
            base = base_latency.get(ep, 110.0)

            # Seasonality depends on hour-of-day
            seasonal = _daily_seasonality(ts.hour, cfg.daily_amplitude_ms)

            # Random noise
            noise = rng.gauss(0.0, cfg.noise_std_ms)

            value = base + seasonal + noise

            # Optional incident (score window only)
            if apply_incident and ep in cfg.incident_endpoints and _is_in_incident_window(ts, cfg, score_start):
                value = (value * cfg.incident_multiplier)

                # Add a sharp spike at the incident start moment
                incident_start = datetime(ts.year, ts.month, ts.day, cfg.incident_start_hour, 0, 0)
                if ts == incident_start:
                    value += cfg.incident_spike_ms

            # Clamp to non-negative
            if value < 1.0:
                value = 1.0

            rows.append(
                {
                    "timestamp": ts.isoformat(),
                    "entity_id": ep,
                    "metric": cfg.metric,
                    "value": f"{value:.3f}",
                }
            )

        ts += step

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "entity_id", "metric", "value"])
        writer.writeheader()
        writer.writerows(rows)


def generate_train_and_score(
    *,
    train_out: str,
    score_out: str,
    cfg: DemoConfig,
) -> None:
    """
    Generate a training dataset (no incident) and a score dataset (with incident).
    """
    # Training window: [start, start+train_days)
    train_start = cfg.start
    generate_events_csv(
        train_out,
        cfg=cfg,
        window_start=train_start,
        days=cfg.train_days,
        apply_incident=False,
    )

    # Score window: [start+train_days, start+train_days+score_days)
    score_start = cfg.start + timedelta(days=cfg.train_days)
    generate_events_csv(
        score_out,
        cfg=cfg,
        window_start=score_start,
        days=cfg.score_days,
        apply_incident=True,
    )
