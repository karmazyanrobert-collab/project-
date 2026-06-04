"""Local file-based event stream producer."""

from __future__ import annotations

import json
import random
import time
import uuid
from datetime import datetime

from faker import Faker

from src.config import STREAM_EVENT_TYPES, ensure_directories
from streaming.stream_config import EVENT_STREAM_PATH, PRODUCER_INTERVAL_SECONDS

fake = Faker()
BUILDINGS = [f"B{i}" for i in range(1, 6)]
ROOMS = [f"R-B{b}-{n:02d}" for b in range(1, 6) for n in range(1, 7)]


def generate_event() -> dict:
    """Generate a single streaming event."""
    event_type = random.choice(STREAM_EVENT_TYPES)
    event = {
        "event_id": str(uuid.uuid4()),
        "student_id": random.randint(1, 300),
        "event_type": event_type,
        "building_id": random.choice(BUILDINGS),
        "room_id": random.choice(ROOMS),
        "event_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    return event


def run_producer(stop_event=None) -> None:
    """Continuously generate events and append to the JSONL stream file."""
    ensure_directories()
    EVENT_STREAM_PATH.parent.mkdir(parents=True, exist_ok=True)

    print("[Producer] Started. Writing events to", EVENT_STREAM_PATH)

    while stop_event is None or not stop_event.is_set():
        event = generate_event()
        with open(EVENT_STREAM_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        print(f"[Producer] {event['event_type']} | student={event['student_id']}")
        time.sleep(PRODUCER_INTERVAL_SECONDS)

    print("[Producer] Stopped.")


if __name__ == "__main__":
    try:
        run_producer()
    except KeyboardInterrupt:
        print("\n[Producer] Interrupted.")
