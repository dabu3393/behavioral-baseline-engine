from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from baseline_engine.baseline import key_from_event
from baseline_engine.config import BaselineConfig
from baseline_engine.models import AnomalyResult, Event
from baseline_engine.scoring import score_event
from baseline_engine.storage_sqlite import BaselineStore


@dataclass(frozen=True)
class ReportStats:
    total_events: int
    scored: int
    skipped_no_baseline: int
    anomalies: int


def score_events_with_store(
    events: List[Event],
    store: BaselineStore,
    config: BaselineConfig,
) -> Tuple[List[AnomalyResult], ReportStats]:
    results: List[AnomalyResult] = []
    scored = 0
    skipped = 0
    anomalies = 0

    for e in events:
        key_str = key_from_event(e, config).as_str()
        baseline = store.get_latest(key_str)
        if baseline is None:
            skipped += 1
            continue

        r = score_event(e, baseline, config)
        results.append(r)
        scored += 1
        if r.is_anomaly:
            anomalies += 1

    stats = ReportStats(
        total_events=len(events),
        scored=scored,
        skipped_no_baseline=skipped,
        anomalies=anomalies,
    )
    return results, stats


def aggregate_anomalies_by_entity(results: List[AnomalyResult]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for r in results:
        if not r.is_anomaly:
            continue
        ent = r.event.entity_id
        counts[ent] = counts.get(ent, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: (-x[1], x[0])))


def aggregate_anomalies_by_hour(results: List[AnomalyResult], *, enabled: bool) -> Dict[int, int]:
    if not enabled:
        return {}
    counts: Dict[int, int] = {}
    for r in results:
        if not r.is_anomaly:
            continue
        h = r.event.timestamp.hour
        counts[h] = counts.get(h, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: x[0]))


def top_anomalies(results: List[AnomalyResult], n: int = 10) -> List[AnomalyResult]:
    anoms = [r for r in results if r.is_anomaly]
    anoms.sort(key=lambda r: r.score, reverse=True)
    return anoms[:n]


def render_markdown_report(
    *,
    input_path: str,
    db_path: str,
    config: BaselineConfig,
    stats: ReportStats,
    by_entity: Dict[str, int],
    by_hour: Dict[int, int],
    top: List[AnomalyResult],
) -> str:
    scored_rate = (stats.scored / stats.total_events * 100.0) if stats.total_events else 0.0
    anomaly_rate = (stats.anomalies / stats.scored * 100.0) if stats.scored else 0.0

    lines: List[str] = []
    lines.append("# Baseline Engine Report")
    lines.append("")
    lines.append("## Run metadata")
    lines.append(f"- Input: `{input_path}`")
    lines.append(f"- DB: `{db_path}`")
    lines.append(f"- use_hour_of_day: `{config.use_hour_of_day}`")
    lines.append(f"- mad_threshold: `{config.mad_threshold}`")
    lines.append(f"- min_samples: `{config.min_samples}`")
    lines.append(f"- min_mad: `{config.min_mad}`")
    lines.append("")

    lines.append("## Coverage")
    lines.append(f"- Total events: **{stats.total_events}**")
    lines.append(f"- Scored (baseline available): **{stats.scored}** ({scored_rate:.1f}%)")
    lines.append(f"- Skipped (no baseline): **{stats.skipped_no_baseline}**")
    lines.append("")

    lines.append("## Anomaly summary")
    lines.append(f"- Anomalies: **{stats.anomalies}**")
    lines.append(f"- Anomaly rate (of scored): **{anomaly_rate:.1f}%**")
    lines.append("")

    lines.append("### Anomalies by entity")
    if not by_entity:
        lines.append("_None_")
    else:
        for ent, cnt in by_entity.items():
            lines.append(f"- `{ent}`: {cnt}")
    lines.append("")

    if config.use_hour_of_day:
        lines.append("### Anomalies by hour")
        if not by_hour:
            lines.append("_None_")
        else:
            for hour, cnt in by_hour.items():
                lines.append(f"- {hour:02d}:00: {cnt}")
        lines.append("")

    lines.append("## Top anomalies")
    if not top:
        lines.append("_None_")
    else:
        lines.append("| score | entity | metric | value | baseline median | baseline MAD | key | time |")
        lines.append("|---:|---|---|---:|---:|---:|---|---|")
        for r in top:
            lines.append(
                f"| {r.score:.2f} | `{r.event.entity_id}` | `{r.event.metric}` | {r.event.value:.2f} "
                f"| {r.baseline.median:.2f} | {r.baseline.mad:.4f} | `{r.baseline.key.as_str()}` | {r.event.timestamp.isoformat()} |"
            )
        lines.append("")
        lines.append("### Notes")
        lines.append("- Scores are measured in MAD units: `|value - median| / MAD`.")
        lines.append("- A baseline must exist for the derived key; otherwise the event is skipped.")
        lines.append("")

    return "\n".join(lines)
