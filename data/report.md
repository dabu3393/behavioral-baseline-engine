# Baseline Engine Report

## Run metadata
- Input: `data/score.csv`
- DB: `data/baselines.db`
- use_hour_of_day: `True`
- mad_threshold: `3.5`
- min_samples: `30`
- min_mad: `1e-06`

## Coverage
- Total events: **1728**
- Scored (baseline available): **1728** (100.0%)
- Skipped (no baseline): **0**

## Anomaly summary
- Anomalies: **138**
- Anomaly rate (of scored): **8.0%**

### Anomalies by entity
- `/checkout`: 60
- `/login`: 55
- `/search`: 23

### Anomalies by hour
- 00:00: 1
- 01:00: 1
- 02:00: 2
- 03:00: 2
- 04:00: 2
- 05:00: 7
- 06:00: 3
- 07:00: 2
- 12:00: 1
- 13:00: 25
- 14:00: 24
- 15:00: 24
- 16:00: 25
- 17:00: 2
- 18:00: 1
- 19:00: 1
- 20:00: 4
- 21:00: 2
- 22:00: 6
- 23:00: 3

## Top anomalies
| score | entity | metric | value | baseline median | baseline MAD | key | time |
|---:|---|---|---:|---:|---:|---|---|
| 49.94 | `/login` | `latency_p95_ms` | 351.70 | 129.73 | 4.4445 | `/login:latency_p95_ms:hour=13` | 2026-01-08T13:00:00 |
| 42.41 | `/checkout` | `latency_p95_ms` | 419.06 | 173.29 | 5.7945 | `/checkout:latency_p95_ms:hour=13` | 2026-01-08T13:00:00 |
| 31.82 | `/checkout` | `latency_p95_ms` | 332.52 | 175.05 | 4.9490 | `/checkout:latency_p95_ms:hour=14` | 2026-01-08T14:20:00 |
| 31.26 | `/checkout` | `latency_p95_ms` | 329.75 | 175.05 | 4.9490 | `/checkout:latency_p95_ms:hour=14` | 2026-01-08T14:40:00 |
| 31.05 | `/checkout` | `latency_p95_ms` | 339.93 | 173.81 | 5.3505 | `/checkout:latency_p95_ms:hour=15` | 2026-01-08T15:40:00 |
| 30.98 | `/checkout` | `latency_p95_ms` | 339.56 | 173.81 | 5.3505 | `/checkout:latency_p95_ms:hour=15` | 2026-01-08T15:25:00 |
| 30.50 | `/checkout` | `latency_p95_ms` | 337.01 | 173.81 | 5.3505 | `/checkout:latency_p95_ms:hour=15` | 2026-01-08T15:55:00 |
| 30.35 | `/checkout` | `latency_p95_ms` | 325.26 | 175.05 | 4.9490 | `/checkout:latency_p95_ms:hour=14` | 2026-01-08T14:00:00 |
| 30.19 | `/checkout` | `latency_p95_ms` | 324.44 | 175.05 | 4.9490 | `/checkout:latency_p95_ms:hour=14` | 2026-01-08T14:50:00 |
| 29.40 | `/checkout` | `latency_p95_ms` | 331.08 | 173.81 | 5.3505 | `/checkout:latency_p95_ms:hour=15` | 2026-01-08T15:05:00 |
| 29.10 | `/checkout` | `latency_p95_ms` | 319.09 | 175.05 | 4.9490 | `/checkout:latency_p95_ms:hour=14` | 2026-01-08T14:05:00 |
| 28.42 | `/checkout` | `latency_p95_ms` | 315.71 | 175.05 | 4.9490 | `/checkout:latency_p95_ms:hour=14` | 2026-01-08T14:10:00 |
| 28.22 | `/checkout` | `latency_p95_ms` | 314.71 | 175.05 | 4.9490 | `/checkout:latency_p95_ms:hour=14` | 2026-01-08T14:25:00 |
| 27.80 | `/checkout` | `latency_p95_ms` | 322.54 | 173.81 | 5.3505 | `/checkout:latency_p95_ms:hour=15` | 2026-01-08T15:20:00 |
| 27.62 | `/checkout` | `latency_p95_ms` | 311.73 | 175.05 | 4.9490 | `/checkout:latency_p95_ms:hour=14` | 2026-01-08T14:35:00 |

### Notes
- Scores are measured in MAD units: `|value - median| / MAD`.
- A baseline must exist for the derived key; otherwise the event is skipped.
