"""Run streaming demo with producer and consumer in parallel."""

import signal
import sys
import threading
import time

from streaming.event_consumer import run_consumer
from streaming.event_producer import run_producer


def main() -> None:
    """Start producer and consumer threads until Ctrl+C."""
    stop_event = threading.Event()

    def handle_interrupt(signum, frame):
        print("\n\nStopping streaming demo...")
        stop_event.set()

    signal.signal(signal.SIGINT, handle_interrupt)

    print("=" * 60)
    print("  University Data Platform — Streaming Demo")
    print("=" * 60)
    print()
    print("Producer generates events every 1 second.")
    print("Consumer reads events and updates DuckDB metrics.")
    print()
    print("Open dashboard in another terminal:")
    print("  streamlit run dashboard/app.py")
    print()
    print("Press Ctrl+C to stop.")
    print("=" * 60)
    print()

    producer_thread = threading.Thread(
        target=run_producer, args=(stop_event,), daemon=True
    )
    consumer_thread = threading.Thread(
        target=run_consumer, args=(stop_event,), daemon=True
    )

    producer_thread.start()
    time.sleep(0.5)
    consumer_thread.start()

    try:
        while not stop_event.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        stop_event.set()

    producer_thread.join(timeout=3)
    consumer_thread.join(timeout=3)
    print("\nStreaming demo stopped.")


if __name__ == "__main__":
    main()
