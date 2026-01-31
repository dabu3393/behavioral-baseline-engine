from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable, List

from baseline_engine.models import Event


def _read_jsonl(path: Path) -> List[Event]:
    events: List[Event] = []
    with path.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON on line {lineno} in {path}: {e}") from e
            events.append(Event.model_validate(obj))
    return events


def _read_csv(path: Path) -> List[Event]:
    """
    Expected headers:
      timestamp,entity_id,metric,value
    Optional:
      tags (JSON object as a string)
    """
    events: List[Event] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        required = {"timestamp", "entity_id", "metric", "value"}
        if reader.fieldnames is None:
            raise ValueError(f"CSV file has no header row: {path}")
        missing = required - set(reader.fieldnames)
        if missing:
            raise ValueError(f"CSV missing required columns {sorted(missing)} in {path}")

        for row in reader:
            obj = {
                "timestamp": row["timestamp"],
                "entity_id": row["entity_id"],
                "metric": row["metric"],
                "value": float(row["value"]),
            }

            tags_raw = row.get("tags")
            if tags_raw:
                try:
                    obj["tags"] = json.loads(tags_raw)
                except json.JSONDecodeError:
                    # If tags are malformed, fail loudly (baseline-first systems hate ambiguity).
                    raise ValueError(f"Invalid tags JSON in CSV row: {tags_raw}")

            events.append(Event.model_validate(obj))
    return events


def load_events(path_str: str) -> List[Event]:
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        return _read_jsonl(path)
    if suffix == ".csv":
        return _read_csv(path)

    raise ValueError(f"Unsupported input format '{suffix}'. Use .csv or .jsonl")
