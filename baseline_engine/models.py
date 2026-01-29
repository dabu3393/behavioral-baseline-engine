from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class Event(BaseModel):
    """
    A single observed data point.

    This is intentionally generic so the engine can be reused
    across domains (latency, auth failures, DNS volume, etc.).
    """

    timestamp: datetime
    entity_id: str
    metric: str
    value: float
    tags: Dict[str, Any] = Field(default_factory=dict)


class BaselineKey(BaseModel):
    """
    Identifies the slice of behavior we learn 'normal' for.
    """

    entity_id: str
    metric: str
    hour_of_day: Optional[int] = None

    def as_str(self) -> str:
        """
        Stable string form for storage and logging.
        """
        if self.hour_of_day is None:
            return f"{self.entity_id}:{self.metric}"
        return f"{self.entity_id}:{self.metric}:hour={self.hour_of_day}"


class BaselineStats(BaseModel):
    """
    Learned definition of normal behavior for a BaselineKey.
    """

    key: BaselineKey

    median: float
    mad: float

    sample_count: int

    training_start: datetime
    training_end: datetime

    created_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1


class AnomalyResult(BaseModel):
    """
    Result of scoring a new event against a baseline.
    """

    event: Event
    baseline: BaselineStats

    score: float
    is_anomaly: bool

    explanation: str
