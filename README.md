# Behavioral Baseline Engine — Baseline-First Detection

**A defensive-first detection engine that learns normal behavior, persists it as an inspectable artifact, and scores new events with explainable deviation logic instead of hard-coded alerts.**

This project focuses on **how detection decisions are made**, not just whether something crosses a threshold. The goal was to design a system that can calmly explain *why* behavior is unusual before anyone decides to alert.

---

## Table of Contents

1. [Overview / Why This Exists](#overview--why-this-exists)
2. [Architecture & Data Flow](#architecture--data-flow)
3. [Design Strategy](#design-strategy)
4. [What I Chose to Do (and What I Didn’t)](#what-i-chose-to-do-and-what-i-didnt)
5. [Outputs & Observability](#outputs--observability)
6. [Rules & Signals](#rules--signals)
7. [False Positives, Gaps, and Surprises](#false-positives-gaps-and-surprises)
8. [Project Structure](#project-structure)
9. [Tech Stack](#tech-stack)
10. [How to Run / Develop](#how-to-run--develop)
11. [Future Improvements / Roadmap](#future-improvements--roadmap)
12. [Closing Thoughts](#closing-thoughts)

---

## Overview / Why This Exists

Most detection systems begin with alerts.

Thresholds are chosen early, alerts are tuned later, and “normal” is often inferred implicitly from what fires too often. I wanted to reverse that order.

This project exists to answer a simpler, more defensive question first:

> Before deciding something is suspicious, can I clearly explain what normal looks like and how far away this behavior actually is?

The Behavioral Baseline Engine is built around the idea that **baselines are the primary artifact**, not alerts. Alerts, severity, and response can come later. If the system cannot explain normal behavior, it has no business deciding what is abnormal.

---

## Architecture & Data Flow

At a high level, the system works as follows:

1. **Event ingestion**

   * Events are read from CSV or JSONL files.
   * Each event includes a timestamp, entity identifier, metric name, and value.

2. **Baseline training**

   * Historical events are grouped into contextual buckets (for example, by entity, metric, and hour-of-day).
   * For each bucket with sufficient data, the engine computes a robust baseline using median and median absolute deviation (MAD).

3. **Baseline persistence**

   * Baselines are stored as durable artifacts in a local SQLite database.
   * Multiple versions of the same baseline can coexist over time.

4. **Scoring**

   * New events are scored against the most recent matching baseline.
   * Scores are expressed in MAD units, with a clear explanation of the deviation.

5. **Inspection & reporting**

   * Baselines can be listed and inspected directly.
   * Individual scoring decisions can be explained.
   * Aggregate results can be summarized into a Markdown report.

This flow favors **inspectability and reasoning** over speed or automation.

---

## Design Strategy

This project is intentionally not a streaming system or a real-time alerting platform.

Instead, the design emphasizes:

* Clear separation of concerns (ingestion, training, storage, scoring).
* Explicit data models rather than implicit assumptions.
* Deterministic, testable behavior at each step.
* Outputs that can be reviewed by a human without needing a UI.

The system is meant to feel like an internal security tool, not a black box.

---

## What I Chose to Do (and What I Didn’t)

### Chosen

* **Baseline-first logic**
  Normal behavior is learned explicitly before any scoring occurs.

* **Robust statistics**
  Median and MAD were chosen to reduce sensitivity to outliers and transient spikes.

* **Durable baselines**
  Learned baselines are stored as versioned artifacts rather than recalculated on every run.

* **Explainability**
  Every score includes a human-readable explanation of how it was computed.

* **Synthetic demo data**
  A built-in generator creates realistic, repeatable datasets with seasonality and injected incidents.

### Not Chosen

* Real-time ingestion or alerting
* Machine learning models that obscure reasoning
* Automatic baseline overwrites
* Hidden thresholds or magic constants
* External services or cloud dependencies

These omissions were intentional to keep the system auditable and defensible.

---

## Outputs & Observability

The engine produces several inspectable outputs:

* **Baseline artifacts**
  Stored in SQLite and viewable via CLI commands.

* **Scoring output (JSONL)**
  Each scored event includes the score, decision, and explanation.

* **Markdown reports**
  Aggregate summaries suitable for case studies or post-incident review.

Example report sections include:

* Coverage (scored vs skipped events)
* Anomaly counts and rates
* Anomalies by entity and hour-of-day
* Top deviations with context

Screenshots are intentionally omitted; outputs are designed to be readable directly.

---

## Rules & Signals

This project does not define alerts.

Instead, it produces **signals**:

* A numeric deviation score (in MAD units).
* A binary anomaly flag based on a configurable threshold.
* A textual explanation tying the event back to its baseline.

This separation allows downstream systems or analysts to decide:

* When to alert
* How to prioritize
* What context matters

The engine’s responsibility ends at **measurement and explanation**.

---

## False Positives, Gaps, and Surprises

Several things became clear while building and testing the system:

* **Context reduces data quickly**
  Adding hour-of-day bucketing dramatically increases baseline specificity, which in turn increases training data requirements.

* **Training sufficiency matters more than math**
  Many “missing baseline” cases were caused by insufficient history, not bugs.

* **Explainability exposes assumptions**
  When every decision must be explained, weak assumptions become obvious very quickly.

* **Baselines change over time**
  Treating baselines as versioned artifacts feels more honest than constantly overwriting “normal.”

These gaps are not failures; they are signals about where operational care is required.

---

## Project Structure

```
behavioral-baseline-engine/
├── baseline_engine/
│   ├── __init__.py            # Package initialization
│   ├── cli.py                 # Command-line interface
│   ├── config.py              # Configuration management
│   ├── models.py              # Core data models
│   ├── baseline.py            # Baseline computation logic
│   ├── scoring.py             # Deviation scoring
│   ├── storage_sqlite.py      # Baseline persistence layer
│   ├── ingest.py              # CSV / JSONL ingestion
│   ├── demo_data.py           # Synthetic dataset generator
│   ├── reporting.py           # Markdown report generation
│   └── explain.py             # Single-event explanation logic
├── tests/                     # Unit and CLI tests
├── data/                      # Sample data files
├── README.md
├── requirements.txt           # Python dependencies
└── pyproject.toml
```

Tests cover individual components and end-to-end flows.

---

## Tech Stack

**Core**

* Python
* Pydantic
* SQLite

**CLI & Tooling**

* Argparse
* Pytest

**Design Choices**

* File-based inputs
* Local persistence
* No external services

---

## How to Run / Develop

Typical local flow:

1. Generate demo data.
2. Train baselines from historical data.
3. Score new events.
4. Inspect baselines or explain specific decisions.
5. Generate a Markdown report.

All commands are executed locally via the CLI.
Sensitive configuration, credentials, and deployment details are intentionally excluded.

---

## Future Improvements / Roadmap

Potential next steps include:

* Baseline comparison across time windows
* Confidence scoring based on sample size
* Event selection helpers for investigation workflows
* Optional visualization layers
* Integration with downstream alerting systems

These are deliberately out of scope for the current project.

---

## Closing Thoughts

This project changed how I think about detection.

I no longer start with “what should alert.”
I start with:

> “What does normal look like, and can I explain it clearly?”

By treating baselines as durable, inspectable artifacts, detection becomes less reactive and more defensible. Alerts become a policy decision layered on top of understanding, not a substitute for it.
