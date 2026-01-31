from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple

from baseline_engine.baseline import key_from_event
from baseline_engine.config import BaselineConfig
from baseline_engine.models import AnomalyResult, Event
from baseline_engine.scoring import score_event
from baseline_engine.storage_sqlite import BaselineStore


def find_event(
    events: List[Event],
    *,
    timestamp: datetime,
    entity_id: str,
    metric: str,
) -> Optional[Event]:
    """
    Find the first event matching timestamp + entity_id + metric.
    Timestamp match is exact ISO equality (so it should match your CSV/JSONL values).
    """
    for e in events:
        if e.timestamp == timestamp and e.entity_id == entity_id and e.metric == metric:
            return e
    return None


def explain_event(
    event: Event,
    store: BaselineStore,
    config: BaselineConfig,
) -> Tuple[str, AnomalyResult | None]:
    """
    Returns a human-readable explanation string and (if baseline exists) an AnomalyResult.
    """
    key_str = key_from_event(event, config).as_str()
    baseline = store.get_latest(key_str)
    if baseline is None:
        msg = (
            "No baseline found for this event.\n"
            f"- Derived key: {key_str}\n"
            "This usually means you didn't train enough history for that key "
            "(or hour-of-day bucketing is different than training)."
        )
        return msg, None

    result = score_event(event, baseline, config)

    msg = (
        "Explain result\n"
        f"- Event: {event.timestamp.isoformat()} {event.entity_id} {event.metric} value={event.value:.2f}\n"
        f"- Derived key: {key_str}\n"
        f"- Baseline: median={baseline.median:.2f}, MAD={baseline.mad:.4f}, samples={baseline.sample_count}\n"
        f"- Score: {result.score:.2f} MAD units\n"
        f"- Threshold: {config.mad_threshold:.2f}\n"
        f"- Decision: {'ANOMALY' if result.is_anomaly else 'normal'}\n"
        f"- Why: {result.explanation}\n"
    )
    return msg, result
