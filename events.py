"""
Lightweight in-process pub/sub event bus.

Simulates TMF event notifications without any external broker.
Subscribers are plain callables; events are plain dicts.  The hub
endpoint exposes a rolling log so Swagger users can see events fire.
"""

from collections import deque
from datetime import datetime, timezone
from typing import Any, Callable

# Rolling log of the last 200 events — visible via GET /hub
_event_log: deque[dict[str, Any]] = deque(maxlen=200)

# topic -> list of subscriber callables
_subscribers: dict[str, list[Callable[[dict[str, Any]], None]]] = {}


def subscribe(topic: str, handler: Callable[[dict[str, Any]], None]) -> None:
    _subscribers.setdefault(topic, []).append(handler)


def publish(topic: str, payload: dict[str, Any]) -> None:
    event = {
        "eventType": topic,
        "eventTime": datetime.now(timezone.utc).isoformat(),
        "event": payload,
    }
    _event_log.appendleft(event)
    for handler in _subscribers.get(topic, []):
        try:
            handler(event)
        except Exception:
            pass  # never let a broken subscriber kill the request


def get_event_log() -> list[dict[str, Any]]:
    return list(_event_log)
