from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional, Sequence

from baseline_engine.models import BaselineKey, BaselineStats


def _dt_to_iso(dt: datetime) -> str:
    # Store as ISO 8601 text for portability and readability.
    return dt.isoformat()


def _iso_to_dt(s: str) -> datetime:
    # datetime.fromisoformat supports timezone offsets if present.
    return datetime.fromisoformat(s)


@dataclass(frozen=True)
class SQLiteConfig:
    path: str = "baselines.db"


class BaselineStore:
    """
    SQLite-backed baseline artifact store.
    """

    def __init__(self, db_path: str = "baselines.db") -> None:
        self.db_path = db_path

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS baselines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    key_str TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    metric TEXT NOT NULL,
                    hour_of_day INTEGER,

                    median REAL NOT NULL,
                    mad REAL NOT NULL,
                    sample_count INTEGER NOT NULL,

                    training_start TEXT NOT NULL,
                    training_end TEXT NOT NULL,

                    created_at TEXT NOT NULL,
                    version INTEGER NOT NULL,

                    UNIQUE(key_str, version, created_at)
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_baselines_key_str ON baselines(key_str);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_baselines_entity_metric ON baselines(entity_id, metric);"
            )
            conn.commit()

    def insert_baseline(self, baseline: BaselineStats) -> None:
        k = baseline.key
        key_str = k.as_str()

        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO baselines (
                    key_str, entity_id, metric, hour_of_day,
                    median, mad, sample_count,
                    training_start, training_end,
                    created_at, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    key_str,
                    k.entity_id,
                    k.metric,
                    k.hour_of_day,
                    float(baseline.median),
                    float(baseline.mad),
                    int(baseline.sample_count),
                    _dt_to_iso(baseline.training_start),
                    _dt_to_iso(baseline.training_end),
                    _dt_to_iso(baseline.created_at),
                    int(baseline.version),
                ),
            )
            conn.commit()

    def insert_many(self, baselines: Iterable[BaselineStats]) -> None:
        rows = []
        for b in baselines:
            k = b.key
            rows.append(
                (
                    k.as_str(),
                    k.entity_id,
                    k.metric,
                    k.hour_of_day,
                    float(b.median),
                    float(b.mad),
                    int(b.sample_count),
                    _dt_to_iso(b.training_start),
                    _dt_to_iso(b.training_end),
                    _dt_to_iso(b.created_at),
                    int(b.version),
                )
            )

        with self.connect() as conn:
            conn.executemany(
                """
                INSERT OR IGNORE INTO baselines (
                    key_str, entity_id, metric, hour_of_day,
                    median, mad, sample_count,
                    training_start, training_end,
                    created_at, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                rows,
            )
            conn.commit()

    def list_baselines(self, key_str: Optional[str] = None) -> List[BaselineStats]:
        query = "SELECT * FROM baselines"
        params: Sequence[object] = ()
        if key_str is not None:
            query += " WHERE key_str = ?"
            params = (key_str,)
        query += " ORDER BY created_at ASC"

        with self.connect() as conn:
            rows = conn.execute(query, params).fetchall()

        return [self._row_to_baseline(r) for r in rows]

    def get_latest(self, key_str: str) -> Optional[BaselineStats]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM baselines
                WHERE key_str = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (key_str,),
            ).fetchone()

        return self._row_to_baseline(row) if row is not None else None

    def list_keys(self) -> List[str]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT DISTINCT key_str
                FROM baselines
                ORDER BY key_str ASC
                """
            ).fetchall()
        return [r["key_str"] for r in rows]

    def count_by_key(self) -> List[tuple[str, int]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT key_str, COUNT(*) as cnt
                FROM baselines
                GROUP BY key_str
                ORDER BY key_str ASC
                """
            ).fetchall()
        return [(r["key_str"], int(r["cnt"])) for r in rows]

    def _row_to_baseline(self, row: sqlite3.Row) -> BaselineStats:
        key = BaselineKey(
            entity_id=row["entity_id"],
            metric=row["metric"],
            hour_of_day=row["hour_of_day"],
        )

        return BaselineStats(
            key=key,
            median=float(row["median"]),
            mad=float(row["mad"]),
            sample_count=int(row["sample_count"]),
            training_start=_iso_to_dt(row["training_start"]),
            training_end=_iso_to_dt(row["training_end"]),
            created_at=_iso_to_dt(row["created_at"]),
            version=int(row["version"]),
        )
