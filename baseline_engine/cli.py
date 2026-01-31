from __future__ import annotations

import argparse
import json
from typing import List
from datetime import datetime

from baseline_engine.baseline import key_from_event, train_baselines
from baseline_engine.config import BaselineConfig
from baseline_engine.ingest import load_events
from baseline_engine.scoring import score_event
from baseline_engine.storage_sqlite import BaselineStore
from baseline_engine.demo_data import DemoConfig, generate_train_and_score
from baseline_engine.explain import explain_event, find_event
from baseline_engine.reporting import (
    aggregate_anomalies_by_entity,
    aggregate_anomalies_by_hour,
    render_markdown_report,
    score_events_with_store,
    top_anomalies,
)



def cmd_hello(_: argparse.Namespace) -> int:
    print("baseline-engine: ok")
    return 0


def cmd_train(args: argparse.Namespace) -> int:
    cfg = BaselineConfig(
        use_hour_of_day=not args.no_hour_of_day,
        mad_threshold=args.mad_threshold,
        min_samples=args.min_samples,
        min_mad=args.min_mad,
    )

    events = load_events(args.input)
    if not events:
        print("No events found. Nothing to train.")
        return 0

    baselines = train_baselines(events, cfg)
    store = BaselineStore(args.db)
    store.init_db()
    store.insert_many(baselines)

    print(f"Trained baselines: {len(baselines)}")
    print(f"DB: {args.db}")
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    cfg = BaselineConfig(
        use_hour_of_day=not args.no_hour_of_day,
        mad_threshold=args.mad_threshold,
        min_samples=args.min_samples,
        min_mad=args.min_mad,
    )

    events = load_events(args.input)
    if not events:
        print("No events found. Nothing to score.")
        return 0

    store = BaselineStore(args.db)
    store.init_db()

    scored = 0
    skipped = 0

    # Output as JSONL (one result per line) so you can pipe it later.
    for e in events:
        k = key_from_event(e, cfg).as_str()
        baseline = store.get_latest(k)

        if baseline is None:
            skipped += 1
            if args.verbose:
                print(f"SKIP (no baseline): {k}")
            continue

        result = score_event(e, baseline, cfg)
        scored += 1

        if args.only_anomalies and not result.is_anomaly:
            continue

        print(result.model_dump_json())

    print(f"Scored: {scored} | Skipped (no baseline): {skipped}")
    return 0


def cmd_keys(args: argparse.Namespace) -> int:
    store = BaselineStore(args.db)
    store.init_db()

    keys = store.list_keys()
    for k in keys:
        print(k)

    print(f"Keys: {len(keys)}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    store = BaselineStore(args.db)
    store.init_db()

    counts = store.count_by_key()
    for key_str, cnt in counts:
        print(f"{key_str}\t{cnt}")

    print(f"Keys: {len(counts)}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    store = BaselineStore(args.db)
    store.init_db()

    baseline = store.get_latest(args.key)
    if baseline is None:
        print(f"No baseline found for key: {args.key}")
        return 1

    # Print baseline artifact as JSON (inspectable, pipeable)
    print(baseline.model_dump_json(indent=2))
    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    # Default start date if not provided
    start = datetime.fromisoformat(args.start)

    cfg = DemoConfig(
        start=start,
        train_days=args.train_days,
        score_days=args.score_days,
        interval_minutes=args.interval_minutes,
        seed=args.seed,
        incident_enabled=not args.no_incident,
    )

    generate_train_and_score(train_out=args.train_out, score_out=args.score_out, cfg=cfg)

    print(f"Wrote train dataset: {args.train_out}")
    print(f"Wrote score dataset: {args.score_out}")
    return 0

def cmd_report(args: argparse.Namespace) -> int:
    cfg = BaselineConfig(
        use_hour_of_day=not args.no_hour_of_day,
        mad_threshold=args.mad_threshold,
        min_samples=args.min_samples,
        min_mad=args.min_mad,
    )

    events = load_events(args.input)
    if not events:
        print("No events found. Nothing to report.")
        return 0

    store = BaselineStore(args.db)
    store.init_db()

    results, stats = score_events_with_store(events, store, cfg)

    by_entity = aggregate_anomalies_by_entity(results)
    by_hour = aggregate_anomalies_by_hour(results, enabled=cfg.use_hour_of_day)
    top = top_anomalies(results, n=args.top)

    md = render_markdown_report(
        input_path=args.input,
        db_path=args.db,
        config=cfg,
        stats=stats,
        by_entity=by_entity,
        by_hour=by_hour,
        top=top,
    )

    out_path = args.out
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"Wrote report: {out_path}")
    print(f"Scored: {stats.scored} | Skipped: {stats.skipped_no_baseline} | Anomalies: {stats.anomalies}")
    return 0


def cmd_explain(args: argparse.Namespace) -> int:
    cfg = BaselineConfig(
        use_hour_of_day=not args.no_hour_of_day,
        mad_threshold=args.mad_threshold,
        min_samples=args.min_samples,
        min_mad=args.min_mad,
    )

    events = load_events(args.input)
    if not events:
        print("No events found.")
        return 1

    ts = datetime.fromisoformat(args.timestamp)

    e = find_event(events, timestamp=ts, entity_id=args.entity, metric=args.metric)
    if e is None:
        print("Event not found with the given timestamp/entity/metric.")
        print("Tip: ensure the timestamp exactly matches what's in the file (ISO format).")
        return 1

    store = BaselineStore(args.db)
    store.init_db()

    msg, result = explain_event(e, store, cfg)
    print(msg)

    if args.json and result is not None:
        print(result.model_dump_json(indent=2))

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="baseline",
        description="baseline-engine: baseline-first behavior modeling and deviation scoring",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    hello = sub.add_parser("hello", help="Sanity check command to confirm install + CLI wiring.")
    hello.set_defaults(func=cmd_hello)

    train = sub.add_parser("train", help="Train baselines from events and store them in SQLite.")
    train.add_argument("--input", required=True, help="Path to events file (.csv or .jsonl)")
    train.add_argument("--db", default="baselines.db", help="SQLite db file path")
    train.add_argument("--min-samples", type=int, default=30, help="Minimum samples required per baseline key")
    train.add_argument("--mad-threshold", type=float, default=3.5, help="Threshold (in MAD units) for anomaly flagging")
    train.add_argument("--min-mad", type=float, default=1e-6, help="Clamp MAD to at least this value")
    train.add_argument("--no-hour-of-day", action="store_true", help="Disable hour-of-day bucketing")
    train.set_defaults(func=cmd_train)

    score = sub.add_parser("score", help="Score events against the latest stored baseline per key.")
    score.add_argument("--input", required=True, help="Path to events file (.csv or .jsonl)")
    score.add_argument("--db", default="baselines.db", help="SQLite db file path")
    score.add_argument("--min-samples", type=int, default=30, help="Minimum samples required per baseline key (kept for parity)")
    score.add_argument("--mad-threshold", type=float, default=3.5, help="Threshold (in MAD units) for anomaly flagging")
    score.add_argument("--min-mad", type=float, default=1e-6, help="Clamp MAD to at least this value")
    score.add_argument("--no-hour-of-day", action="store_true", help="Disable hour-of-day bucketing")
    score.add_argument("--only-anomalies", action="store_true", help="Only print anomalous results")
    score.add_argument("--verbose", action="store_true", help="Print skipped keys (no baseline)")
    score.set_defaults(func=cmd_score)

    keys = sub.add_parser("keys", help="Print distinct baseline keys in the DB.")
    keys.add_argument("--db", default="baselines.db", help="SQLite db file path")
    keys.set_defaults(func=cmd_keys)

    lst = sub.add_parser("list", help="List baseline keys with counts (how many versions saved).")
    lst.add_argument("--db", default="baselines.db", help="SQLite db file path")
    lst.set_defaults(func=cmd_list)

    show = sub.add_parser("show", help="Show the latest baseline artifact for a given key_str.")
    show.add_argument("--db", default="baselines.db", help="SQLite db file path")
    show.add_argument("--key", required=True, help="Baseline key string (use `baseline keys` to discover)")
    show.set_defaults(func=cmd_show)

    demo = sub.add_parser("demo", help="Generate demo train/score datasets with seasonality and an injected incident.")
    demo.add_argument("--train-out", default="data/train.csv", help="Output path for training CSV")
    demo.add_argument("--score-out", default="data/score.csv", help="Output path for scoring CSV")
    demo.add_argument("--start", default="2026-01-01T00:00:00", help="ISO start datetime for training window")
    demo.add_argument("--train-days", type=int, default=7, help="Number of training days to generate")
    demo.add_argument("--score-days", type=int, default=2, help="Number of scoring days to generate")
    demo.add_argument("--interval-minutes", type=int, default=5, help="Sampling interval in minutes")
    demo.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    demo.add_argument("--no-incident", action="store_true", help="Disable incident injection in the score window")
    demo.set_defaults(func=cmd_demo)

    report = sub.add_parser("report", help="Score events and write a Markdown report (case-study friendly).")
    report.add_argument("--input", required=True, help="Path to events file (.csv or .jsonl)")
    report.add_argument("--db", default="baselines.db", help="SQLite db file path")
    report.add_argument("--out", default="report.md", help="Output Markdown file path")
    report.add_argument("--top", type=int, default=10, help="How many top anomalies to include")
    report.add_argument("--min-samples", type=int, default=30, help="Minimum samples required per baseline key")
    report.add_argument("--mad-threshold", type=float, default=3.5, help="Threshold (in MAD units) for anomaly flagging")
    report.add_argument("--min-mad", type=float, default=1e-6, help="Clamp MAD to at least this value")
    report.add_argument("--no-hour-of-day", action="store_true", help="Disable hour-of-day bucketing")
    report.set_defaults(func=cmd_report)

    explain = sub.add_parser("explain", help="Explain how a single event was scored (baseline used + score + why).")
    explain.add_argument("--input", required=True, help="Path to events file (.csv or .jsonl)")
    explain.add_argument("--db", default="baselines.db", help="SQLite db file path")

    explain.add_argument("--timestamp", required=True, help="ISO timestamp matching the event row")
    explain.add_argument("--entity", required=True, help="entity_id (e.g., /login)")
    explain.add_argument("--metric", required=True, help="metric name (e.g., latency_p95_ms)")

    explain.add_argument("--json", action="store_true", help="Also print the full AnomalyResult as JSON")
    explain.add_argument("--min-samples", type=int, default=30, help="Minimum samples required per baseline key")
    explain.add_argument("--mad-threshold", type=float, default=3.5, help="Threshold (in MAD units) for anomaly flagging")
    explain.add_argument("--min-mad", type=float, default=1e-6, help="Clamp MAD to at least this value")
    explain.add_argument("--no-hour-of-day", action="store_true", help="Disable hour-of-day bucketing")
    explain.set_defaults(func=cmd_explain)


    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
