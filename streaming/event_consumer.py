"""Local file-based event stream consumer."""

from __future__ import annotations

import json
import time
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path

import duckdb
import pandas as pd

from streaming.stream_config import (
    CONSUMER_POLL_INTERVAL_SECONDS,
    EVENT_STREAM_PATH,
    METRICS_WINDOW_MINUTES,
    WAREHOUSE_DB,
)


def _ensure_streaming_tables(con: duckdb.DuckDBPyConnection) -> None:
    """Create streaming tables if they do not exist."""
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS streaming_events (
            event_id VARCHAR,
            student_id INTEGER,
            event_type VARCHAR,
            building_id VARCHAR,
            room_id VARCHAR,
            event_time TIMESTAMP
        )
        """
    )
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS streaming_metrics (
            metric_name VARCHAR,
            metric_value DOUBLE,
            updated_at TIMESTAMP
        )
        """
    )


def _parse_event_time(value: str) -> datetime:
    """Parse event time string to datetime."""
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def _compute_metrics(recent_events: deque) -> dict[str, float]:
    """Compute streaming metrics from recent events."""
    now = datetime.now()
    window_start = now - timedelta(minutes=METRICS_WINDOW_MINUTES)
    minute_start = now - timedelta(minutes=1)

    events_in_window = [
        e for e in recent_events if _parse_event_time(e["event_time"]) >= window_start
    ]
    events_last_minute = [
        e for e in recent_events if _parse_event_time(e["event_time"]) >= minute_start
    ]

    active_students = len({e["student_id"] for e in events_in_window})
    assignment_submissions = sum(
        1 for e in events_in_window if e["event_type"] == "assignment_submitted"
    )
    building_entries = sum(
        1 for e in events_in_window if e["event_type"] == "entered_building"
    )

    return {
        "events_per_minute": float(len(events_last_minute)),
        "active_students_last_5_min": float(active_students),
        "assignment_submissions_last_5_min": float(assignment_submissions),
        "building_entries_last_5_min": float(building_entries),
    }


def _insert_event(con: duckdb.DuckDBPyConnection, event: dict) -> None:
    """Insert a single event into DuckDB."""
    df = pd.DataFrame([event])
    con.register("_event", df)
    con.execute(
        """
        INSERT INTO streaming_events
        SELECT event_id, student_id, event_type, building_id, room_id,
               CAST(event_time AS TIMESTAMP)
        FROM _event
        """
    )
    con.unregister("_event")


def _update_metrics(con: duckdb.DuckDBPyConnection, metrics: dict[str, float]) -> None:
    """Upsert streaming metrics in DuckDB."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for name, value in metrics.items():
        con.execute(
            "DELETE FROM streaming_metrics WHERE metric_name = ?",
            [name],
        )
        con.execute(
            "INSERT INTO streaming_metrics VALUES (?, ?, ?)",
            [name, value, now],
        )


def run_consumer(stop_event=None) -> None:
    """Tail the event stream file and process new events."""
    WAREHOUSE_DB.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(WAREHOUSE_DB))
    _ensure_streaming_tables(con)

    recent_events: deque = deque(maxlen=10000)
    file_pos = 0

    if EVENT_STREAM_PATH.exists():
        file_pos = EVENT_STREAM_PATH.stat().st_size

    print("[Consumer] Started. Watching", EVENT_STREAM_PATH)

    while stop_event is None or not stop_event.is_set():
        if EVENT_STREAM_PATH.exists():
            with open(EVENT_STREAM_PATH, "r", encoding="utf-8") as f:
                f.seek(file_pos)
                new_lines = f.readlines()
                file_pos = f.tell()

            for line in new_lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    _insert_event(con, event)
                    recent_events.append(event)
                except json.JSONDecodeError:
                    continue

            if new_lines:
                metrics = _compute_metrics(recent_events)
                _update_metrics(con, metrics)
                print(
                    f"[Consumer] Processed {len(new_lines)} events | "
                    f"events/min={metrics['events_per_minute']:.0f} | "
                    f"active={metrics['active_students_last_5_min']:.0f}"
                )

        time.sleep(CONSUMER_POLL_INTERVAL_SECONDS)

    con.close()
    print("[Consumer] Stopped.")


if __name__ == "__main__":
    try:
        run_consumer()
    except KeyboardInterrupt:
        print("\n[Consumer] Interrupted.")
