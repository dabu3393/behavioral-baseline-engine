from __future__ import annotations

from baseline_engine.config import BaselineConfig
from baseline_engine.models import AnomalyResult, BaselineStats, Event


def score_event(
    event: Event,
    baseline: BaselineStats,
    config: BaselineConfig,
) -> AnomalyResult:
    """
    Score a single event against a baseline.

    Returns an AnomalyResult with a numeric score and explanation.
    """

    # Distance from "normal", expressed in MAD units
    deviation = abs(event.value - baseline.median)
    score = deviation / baseline.mad

    is_anomaly = score >= config.mad_threshold

    direction = "above" if event.value > baseline.median else "below"

    explanation = (
        f"Value {event.value:.2f} is {score:.2f} MAD {direction} "
        f"baseline median {baseline.median:.2f} "
        f"for {baseline.key.as_str()}"
    )

    return AnomalyResult(
        event=event,
        baseline=baseline,
        score=score,
        is_anomaly=is_anomaly,
        explanation=explanation,
    )
