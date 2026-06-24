"""
TMF BSS Showcase — main entry point.

A single FastAPI application that mounts three TMF-compliant routers:
  • TMF632  Party Management         /party/v5/…
  • TMF620  Product Catalog          /productCatalog/v4/…
  • TMF622  Product Ordering         /productOrderingManagement/v4/…

Run locally:
    uvicorn main:app --reload

The /docs endpoint (Swagger UI) is the primary showcase interface.
"""

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from services.party import router as party_router
from services.catalog import router as catalog_router
from services.order import router as order_router
from shared.events import get_event_log

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="TMF BSS Showcase",
    description=(
        "A TM Forum Open API–compliant Business Support Systems stack.\n\n"
        "Implements **TMF632** Party Management, **TMF620** Product Catalog, "
        "and **TMF622** Product Ordering with fully stubbed data and a simulated "
        "order fulfilment state machine.\n\n"
        "**Demo flow:**\n"
        "1. `POST /party/v5/individual` — create a contact\n"
        "2. `GET /productCatalog/v4/productOffering` — browse offerings\n"
        "3. `POST /productOrderingManagement/v4/productOrder` — place an order\n"
        "4. `GET /productOrderingManagement/v4/productOrder/{id}` — poll state "
        "as it advances `acknowledged → inProgress → completed`\n"
        "5. `GET /hub` — inspect the event log"
    ),
    version="1.0.0",
    contact={
        "name": "TMF BSS Showcase",
        "url": "https://github.com/your-handle/tmf-bss-showcase",
    },
    license_info={
        "name": "MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(party_router)
app.include_router(catalog_router)
app.include_router(order_router)

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
        "services": ["TMF632", "TMF620", "TMF622"],
    }


# ---------------------------------------------------------------------------
# Event hub (TMF688-style — lightweight read-only log)
# ---------------------------------------------------------------------------

@app.get(
    "/hub",
    tags=["System"],
    summary="Event log (TMF688-style)",
    response_description="Rolling log of the last 200 domain events",
)
def hub() -> JSONResponse:
    """
    Returns a rolling log of every domain event published since the last
    restart.  Events are emitted automatically as orders advance through
    their state machine (`acknowledged → inProgress → completed`).

    This endpoint simulates the TMF688 Event Management notification hub.
    """
    return JSONResponse(content=get_event_log())
