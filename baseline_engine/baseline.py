from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from statistics import median
from typing import Dict, Iterable, List, Tuple

from baseline_engine.config import BaselineConfig
from baseline_engine.models import BaselineKey, BaselineStats, Event


def _utc_now() -> datetime:
    # Use timezone-aware timestamps internally where possible.
    return datetime.now(timezone.utc)


def key_from_event(event: Event, config: BaselineConfig) -> BaselineKey:
    """
    Derive the baseline key for an event based on the configured granularity.
    """
    hour = event.timestamp.hour if config.use_hour_of_day else None
    return BaselineKey(entity_id=event.entity_id, metric=event.metric, hour_of_day=hour)


def group_events(
    events: Iterable[Event],
    config: BaselineConfig,
) -> Dict[str, List[Event]]:
    """
    Group events by derived BaselineKey string.

    We group by the stable string form so storage/logging match grouping behavior.
    """
    groups: Dict[str, List[Event]] = defaultdict(list)
    for e in events:
        k = key_from_event(e, config)
        groups[k.as_str()].append(e)
    return dict(groups)


def compute_median_and_mad(values: List[float], *, min_mad: float) -> Tuple[float, float]:
    """
    Compute robust center (median) and dispersion (MAD).

    MAD = median(|x - median(x)|)

    min_mad guards against division by zero and ultra-flat baselines.
    """
    if not values:
        raise ValueError("compute_median_and_mad() requires at least one value")

    m = float(median(values))
    abs_devs = [abs(v - m) for v in values]
    mad = float(median(abs_devs))
    if mad < min_mad:
        mad = float(min_mad)
    return m, mad


def train_baselines(events: Iterable[Event], config: BaselineConfig) -> List[BaselineStats]:
    """
    Train baselines from a set of events.

    Returns BaselineStats objects (baseline artifacts) that can be persisted.
    """
    groups = group_events(events, config)
    baselines: List[BaselineStats] = []

    for key_str, evts in groups.items():
        if len(evts) < config.min_samples:
            # Baseline-first thinking: if we don't have enough history,
            # we refuse to pretend we know "normal".
            continue

        # Sort by time to define training window
        evts_sorted = sorted(evts, key=lambda e: e.timestamp)

        # Reconstruct the key from the first event (same for entire group)
        k = key_from_event(evts_sorted[0], config)

        values = [float(e.value) for e in evts_sorted]
        med, mad = compute_median_and_mad(values, min_mad=config.min_mad)

        baseline = BaselineStats(
            key=k,
            median=med,
            mad=mad,
            sample_count=len(values),
            training_start=evts_sorted[0].timestamp,
            training_end=evts_sorted[-1].timestamp,
            created_at=_utc_now(),
            version=1,
        )
        baselines.append(baseline)

    return baselines
