"""
TMF BSS Showcase — main entry point.

A single FastAPI application that mounts four TMF-compliant routers:
  • TMF632  Party Management         /party/v5/…
  • TMF620  Product Catalog          /productCatalog/v4/…
  • TMF622  Product Ordering         /productOrderingManagement/v4/…
  • TMF666  Account Management       /accountManagement/v4/…
  • TMF688  Event Management         /hub/…

Run locally:
    uvicorn main:app --reload

The /docs endpoint (Swagger UI) is the primary showcase interface.
"""

import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

from services.party import router as party_router
from services.catalog import router as catalog_router
from services.order import router as order_router
from services.account import router as account_router
from shared.events import (
    get_event_log,
    get_event_stats,
    register_subscription,
    list_subscriptions,
    delete_subscription,
)

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="TMF BSS Showcase",
    description=(
        "A **TM Forum Open API–compliant** Business Support Systems stack "
        "built with Python + FastAPI.\n\n"
        "All data is stubbed in-memory — no external systems are called — "
        "but every API interaction follows TMF Open API specifications exactly.\n\n"
        "---\n\n"
        "### Implemented APIs\n\n"
        "| API | Domain | What it does |\n"
        "|-----|--------|--------------|\n"
        "| **TMF632** | Party Management | Create and manage customer contacts |\n"
        "| **TMF620** | Product Catalog | Browse product specs, offerings, and pricing |\n"
        "| **TMF622** | Product Ordering | Place orders with automatic fulfilment state machine |\n"
        "| **TMF666** | Account Management | Create and manage billing accounts |\n"
        "| **TMF688** | Event Management | Inspect domain events and register subscriptions |\n\n"
        "---\n\n"
        "### Demo walkthrough\n\n"
        "1. **Create a contact** → `POST /party/v5/individual`\n"
        "2. **Browse the catalog** → `GET /productCatalog/v4/productOffering`\n"
        "3. **Place an order** → `POST /productOrderingManagement/v4/productOrder`\n"
        "4. **Watch fulfilment** → `GET /productOrderingManagement/v4/productOrder/{id}` "
        "— poll to see state advance: `acknowledged → inProgress → completed`\n"
        "5. **Inspect events** → `GET /hub` — see every domain event that fired\n"
        "6. **Check stats** → `GET /hub/stats` — event counts by type and domain"
    ),
    version="1.0.0",
    contact={
        "name": "TMF BSS Showcase",
        "url": "https://github.com/allmylearningoeshere/tmf-bss-showcase-01",
    },
    license_info={
        "name": "MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(party_router)
app.include_router(catalog_router)
app.include_router(order_router)
app.include_router(account_router)

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get(
    "/health",
    tags=["System"],
    summary="Health check",
    response_description="Service is up",
)
def health() -> dict:
    """
    Returns `200 OK` with a timestamp.  Used by the hosting platform for
    liveness probes and by recruiters to confirm the service is running.
    """
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "services": ["TMF632", "TMF620", "TMF622", "TMF666", "TMF688"],
    }


# ---------------------------------------------------------------------------
# TMF688 Event Management — Hub endpoints
# ---------------------------------------------------------------------------

@app.get(
    "/hub",
    tags=["TMF688 · Event Management"],
    summary="Query the event log",
    response_description="Filtered, paginated list of domain events",
)
def hub(
    event_type: str | None = Query(
        None,
        alias="eventType",
        description=(
            "Filter by event type, e.g. ProductOrderCreateEvent, "
            "IndividualCreateEvent, ProductOrderStateChangeEvent"
        ),
    ),
    domain: str | None = Query(
        None,
        description="Filter by domain: party, catalog, order",
    ),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=200, description="Page size"),
) -> JSONResponse:
    """
    Returns a rolling log of domain events published since the last
    restart.  Events are emitted automatically on every create, update,
    delete, and order state transition.

    **Filtering:**
    - `eventType` — exact match on the event type name
    - `domain` — filter by domain: `party`, `catalog`, or `order`

    **Pagination:** `offset` and `limit` query parameters.

    **TMF688 spec reference:** GET /hub (event query)
    """
    page, total = get_event_log(
        event_type=event_type,
        domain=domain,
        limit=limit,
        offset=offset,
    )
    return JSONResponse(
        content=page,
        headers={
            "X-Total-Count": str(total),
            "X-Result-Count": str(len(page)),
        },
    )


@app.get(
    "/hub/stats",
    tags=["TMF688 · Event Management"],
    summary="Event statistics",
    response_description="Summary counts by event type and domain",
)
def hub_stats() -> JSONResponse:
    """
    Returns aggregate statistics for the event log:
    total event count, breakdown by event type, and breakdown by domain.

    Useful for dashboards and monitoring.
    """
    return JSONResponse(content=get_event_stats())


# ---------------------------------------------------------------------------
# TMF688 Hub Subscriptions (simulated)
# ---------------------------------------------------------------------------

class HubSubscriptionCreate(BaseModel):
    """Payload for registering a hub subscription."""
    model_config = ConfigDict(populate_by_name=True)

    callback: str = Field(
        ...,
        description="URL to receive event notifications (simulated — no real delivery)",
    )
    query: Optional[str] = Field(
        None,
        description="Optional filter query, e.g. 'eventType=ProductOrderStateChangeEvent'",
    )


@app.post(
    "/hub",
    tags=["TMF688 · Event Management"],
    summary="Register a hub subscription",
    status_code=201,
    response_description="Subscription registered",
)
def create_subscription(body: HubSubscriptionCreate) -> JSONResponse:
    """
    Registers a callback URL to receive event notifications.

    In a production system, the hub would POST events to this callback
    URL as they occur.  In this showcase, subscriptions are stored but
    delivery is simulated — the subscription appears in `GET /hub/subscription`.

    **TMF688 spec reference:** POST /hub
    """
    sub = register_subscription(
        callback=body.callback,
        query=body.query,
    )
    return JSONResponse(content=sub, status_code=201)


@app.get(
    "/hub/subscription",
    tags=["TMF688 · Event Management"],
    summary="List hub subscriptions",
    response_description="Array of registered subscriptions",
)
def get_subscriptions() -> JSONResponse:
    """
    Returns all registered hub subscriptions.

    **TMF688 spec reference:** GET /hub
    """
    return JSONResponse(content=list_subscriptions())


@app.delete(
    "/hub/subscription/{subscription_id}",
    tags=["TMF688 · Event Management"],
    summary="Unregister a hub subscription",
    status_code=204,
    response_description="Subscription removed (no content)",
)
def remove_subscription(subscription_id: str):
    """
    Removes a hub subscription by its ID.

    **TMF688 spec reference:** DELETE /hub/{id}
    """
    result = delete_subscription(subscription_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "ERR_NOT_FOUND",
                "reason": f"Subscription {subscription_id} not found",
                "@type": "Error",
            },
        )
    return None
