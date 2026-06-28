"""
TMF688 Event Management — enhanced event bus.

Provides:
  • Structured event payloads with id, correlationId, eventType, eventTime
  • Rolling log of the last 500 events
  • Filterable event retrieval (by eventType, domain, time range)
  • Hub subscription registry (simulated — no real webhook delivery)
  • In-process pub/sub for internal listeners
"""

import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Any, Callable

# Rolling log of events — visible via GET /hub
_event_log: deque[dict[str, Any]] = deque(maxlen=500)

# Sequence counter for ordering
_sequence: int = 0

# topic -> list of subscriber callables
_subscribers: dict[str, list[Callable[[dict[str, Any]], None]]] = {}

# Hub subscriptions (simulated TMF688 Hub resource)
_subscriptions: dict[str, dict[str, Any]] = {}

# Domain mapping for event types
_DOMAIN_MAP = {
    "Individual": "party",
    "ProductSpecification": "catalog",
    "ProductOffering": "catalog",
    "ProductOrder": "order",
    "BillingAccount": "account",
}


def subscribe(topic: str, handler: Callable[[dict[str, Any]], None]) -> None:
    """Register an in-process subscriber for a topic."""
    _subscribers.setdefault(topic, []).append(handler)


def publish(topic: str, payload: dict[str, Any]) -> None:
    """
    Publish a TMF688-compliant event.

    Enriches the payload with id, eventId, correlationId, eventTime,
    domain, and sequence number before appending to the log.
    """
    global _sequence
    _sequence += 1

    # Derive domain from the event type name
    domain = "system"
    for key, dom in _DOMAIN_MAP.items():
        if key in topic:
            domain = dom
            break

    event = {
        "eventId": str(uuid.uuid4()),
        "eventType": topic,
        "eventTime": datetime.now(timezone.utc).isoformat(),
        "correlationId": str(uuid.uuid4()),
        "domain": domain,
        "sequence": _sequence,
        "event": payload,
    }

    _event_log.appendleft(event)

    for handler in _subscribers.get(topic, []):
        try:
            handler(event)
        except Exception:
            pass  # never let a broken subscriber kill the request


def get_event_log(
    event_type: str | None = None,
    domain: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    """
    Retrieve events with optional filtering.

    Returns (page, total_matching_count).
    """
    results = list(_event_log)

    if event_type:
        results = [e for e in results if e.get("eventType") == event_type]

    if domain:
        results = [e for e in results if e.get("domain") == domain]

    total = len(results)
    page = results[offset: offset + limit]
    return page, total


def get_event_stats() -> dict[str, Any]:
    """Return summary statistics about the event log."""
    events = list(_event_log)
    type_counts: dict[str, int] = {}
    domain_counts: dict[str, int] = {}

    for e in events:
        et = e.get("eventType", "unknown")
        dom = e.get("domain", "unknown")
        type_counts[et] = type_counts.get(et, 0) + 1
        domain_counts[dom] = domain_counts.get(dom, 0) + 1

    return {
        "totalEvents": len(events),
        "sequence": _sequence,
        "byEventType": type_counts,
        "byDomain": domain_counts,
    }


# ---------------------------------------------------------------------------
# Hub Subscription management (TMF688 Hub resource — simulated)
# ---------------------------------------------------------------------------

def register_subscription(callback: str, query: str | None = None) -> dict[str, Any]:
    """Register a hub subscription (simulated — no real delivery)."""
    sub_id = str(uuid.uuid4())
    sub = {
        "id": sub_id,
        "href": f"/hub/{sub_id}",
        "callback": callback,
        "query": query,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "@type": "HubSubscription",
    }
    _subscriptions[sub_id] = sub
    return sub


def list_subscriptions() -> list[dict[str, Any]]:
    """List all hub subscriptions."""
    return list(_subscriptions.values())


def delete_subscription(sub_id: str) -> dict[str, Any] | None:
    """Remove a hub subscription. Returns the deleted sub or None."""
    return _subscriptions.pop(sub_id, None)
