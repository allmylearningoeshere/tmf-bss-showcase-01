"""
TMF622 Product Ordering Management.

Endpoints:
  POST   /productOrderingManagement/v4/productOrder          Place an order
  GET    /productOrderingManagement/v4/productOrder          List orders
  GET    /productOrderingManagement/v4/productOrder/{id}     Retrieve an order
  PATCH  /productOrderingManagement/v4/productOrder/{id}     Update / cancel
  DELETE /productOrderingManagement/v4/productOrder/{id}     Delete an order

The state machine is the showcase centrepiece.  On creation, the order
is set to `acknowledged`.  A background task then advances it through:

    acknowledged  ──(3 s)──▶  inProgress  ──(5 s)──▶  completed

Each transition publishes a TMF688-style ProductOrderStateChangeEvent
to the event bus, visible via GET /hub.

Cancellation is supported via PATCH with state="cancelled", which
halts the state machine.
"""

import uuid
import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse

from shared.store import product_orders
from shared.events import publish
from shared.schemas.tmf622 import (
    ProductOrder,
    ProductOrderCreate,
    ProductOrderUpdate,
)

router = APIRouter(
    prefix="/productOrderingManagement/v4",
    tags=["TMF622 · Product Ordering"],
)

BASE_PATH = "/productOrderingManagement/v4/productOrder"

# Valid TMF622 order states
VALID_STATES = {
    "acknowledged",
    "inProgress",
    "completed",
    "cancelled",
    "partial",
    "failed",
    "held",
    "pending",
    "assessingCancellation",
    "pendingCancellation",
}


# ---------------------------------------------------------------------------
# State machine — background fulfilment simulation
# ---------------------------------------------------------------------------

async def _advance_order(order_id: str) -> None:
    """
    Simulates order fulfilment as a background task.

    Waits 3 seconds, advances to inProgress, waits 5 more seconds,
    advances to completed.  Stops if the order is cancelled or deleted.
    """
    # --- Transition 1: acknowledged → inProgress ---
    await asyncio.sleep(3)

    record = product_orders.get(order_id)
    if not record or record.get("state") != "acknowledged":
        return  # cancelled or deleted in the meantime

    now = datetime.now(timezone.utc).isoformat()
    record["state"] = "inProgress"
    record["lastUpdatedAt"] = now

    # Set each order item state to match
    for item in record.get("orderItem", []):
        item["state"] = "inProgress"

    publish("ProductOrderStateChangeEvent", {
        "productOrder": {
            "id": record["id"],
            "href": record["href"],
            "state": "inProgress",
            "previousState": "acknowledged",
            "transitionTime": now,
        },
    })

    # --- Transition 2: inProgress → completed ---
    await asyncio.sleep(5)

    record = product_orders.get(order_id)
    if not record or record.get("state") != "inProgress":
        return  # cancelled or deleted

    now = datetime.now(timezone.utc).isoformat()
    record["state"] = "completed"
    record["completionDate"] = now
    record["lastUpdatedAt"] = now

    for item in record.get("orderItem", []):
        item["state"] = "completed"

    publish("ProductOrderStateChangeEvent", {
        "productOrder": {
            "id": record["id"],
            "href": record["href"],
            "state": "completed",
            "previousState": "inProgress",
            "transitionTime": now,
        },
    })


# ---------------------------------------------------------------------------
# POST — place an order
# ---------------------------------------------------------------------------

@router.post(
    "/productOrder",
    response_model=ProductOrder,
    status_code=201,
    summary="Place a product order",
    response_description="Order created and fulfilment started",
)
async def create_order(
    body: ProductOrderCreate,
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    """
    Places a new ProductOrder.

    The order is immediately set to `acknowledged` and a background task
    begins simulating fulfilment.  Poll the order via GET to watch the
    state advance:

        acknowledged  →  inProgress  →  completed

    Each transition fires a `ProductOrderStateChangeEvent` visible at
    GET /hub.

    **Minimum payload:** one `orderItem` with a `productOffering` reference.

    **TMF622 spec reference:** POST /productOrder
    """
    order_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    order_data = body.model_dump(by_alias=True, exclude_none=True)

    # Set initial state on each order item
    for item in order_data.get("orderItem", []):
        item["state"] = "acknowledged"

    record = {
        "id": order_id,
        "href": f"{BASE_PATH}/{order_id}",
        "state": "acknowledged",
        "orderDate": now,
        "expectedCompletionDate": None,
        "completionDate": None,
        "lastUpdatedAt": now,
        "@type": "ProductOrder",
        "@baseType": "ProductOrder",
        **order_data,
    }

    product_orders[order_id] = record

    publish("ProductOrderCreateEvent", {
        "productOrder": record,
    })

    # Start the fulfilment state machine
    background_tasks.add_task(_advance_order, order_id)

    return JSONResponse(content=record, status_code=201)


# ---------------------------------------------------------------------------
# GET — list orders
# ---------------------------------------------------------------------------

@router.get(
    "/productOrder",
    response_model=list[ProductOrder],
    summary="List product orders",
    response_description="Array of orders",
)
def list_orders(
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=200, description="Page size"),
    state: str | None = Query(
        None,
        description="Filter by state (acknowledged, inProgress, completed, cancelled)",
    ),
    external_id: str | None = Query(
        None,
        alias="externalId",
        description="Filter by external ID (exact match)",
    ),
) -> JSONResponse:
    """
    Returns a paginated list of all ProductOrders.

    Supports filtering by `state` and `externalId`.

    **TMF622 spec reference:** GET /productOrder
    """
    results = list(product_orders.values())

    if state:
        results = [r for r in results if r.get("state") == state]

    if external_id:
        results = [r for r in results if r.get("externalId") == external_id]

    total = len(results)
    page = results[offset: offset + limit]

    return JSONResponse(
        content=page,
        headers={"X-Total-Count": str(total), "X-Result-Count": str(len(page))},
    )


# ---------------------------------------------------------------------------
# GET — retrieve by id
# ---------------------------------------------------------------------------

@router.get(
    "/productOrder/{order_id}",
    response_model=ProductOrder,
    summary="Retrieve a product order",
    response_description="The requested order with current state",
)
def get_order(order_id: str) -> JSONResponse:
    """
    Returns a single ProductOrder by its ID.

    Poll this endpoint after placing an order to watch the state
    advance through the fulfilment lifecycle.

    **TMF622 spec reference:** GET /productOrder/{id}
    """
    record = product_orders.get(order_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "ERR_NOT_FOUND",
                "reason": f"ProductOrder {order_id} not found",
                "@type": "Error",
            },
        )
    return JSONResponse(content=record)


# ---------------------------------------------------------------------------
# PATCH — update / cancel
# ---------------------------------------------------------------------------

@router.patch(
    "/productOrder/{order_id}",
    response_model=ProductOrder,
    summary="Update or cancel a product order",
    response_description="Updated order",
)
def patch_order(order_id: str, body: ProductOrderUpdate) -> JSONResponse:
    """
    Partially updates a ProductOrder.

    **Cancellation:** set `state` to `"cancelled"` and optionally provide
    a `cancellationReason`.  This halts the background fulfilment task.
    Cancellation is only allowed before the order reaches `completed`.

    **Other updates:** description, category, priority, and notes can be
    modified at any time.

    **TMF622 spec reference:** PATCH /productOrder/{id}
    """
    record = product_orders.get(order_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "ERR_NOT_FOUND",
                "reason": f"ProductOrder {order_id} not found",
                "@type": "Error",
            },
        )

    updates = body.model_dump(by_alias=True, exclude_none=True)
    now = datetime.now(timezone.utc).isoformat()

    # Handle cancellation
    new_state = updates.get("state")
    if new_state:
        if new_state not in VALID_STATES:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "ERR_INVALID_STATE",
                    "reason": f"Invalid state '{new_state}'. Valid states: {', '.join(sorted(VALID_STATES))}",
                    "@type": "Error",
                },
            )

        current_state = record.get("state")
        if current_state == "completed":
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "ERR_STATE_CONFLICT",
                    "reason": "Cannot modify a completed order",
                    "@type": "Error",
                },
            )

        if new_state == "cancelled":
            record["cancellationDate"] = now
            for item in record.get("orderItem", []):
                item["state"] = "cancelled"

            publish("ProductOrderStateChangeEvent", {
                "productOrder": {
                    "id": record["id"],
                    "href": record["href"],
                    "state": "cancelled",
                    "previousState": current_state,
                    "transitionTime": now,
                },
            })

    # Merge notes (append, don't replace)
    if "note" in updates and updates["note"]:
        existing_notes = record.get("note") or []
        for n in updates["note"]:
            n["date"] = n.get("date") or now
            n["id"] = n.get("id") or str(uuid.uuid4())[:8]
        existing_notes.extend(updates["note"])
        record["note"] = existing_notes
        del updates["note"]

    record.update(updates)
    record["lastUpdatedAt"] = now

    return JSONResponse(content=record)


# ---------------------------------------------------------------------------
# DELETE — remove
# ---------------------------------------------------------------------------

@router.delete(
    "/productOrder/{order_id}",
    status_code=204,
    summary="Delete a product order",
    response_description="Order deleted (no content)",
)
def delete_order(order_id: str):
    """
    Removes a ProductOrder from the store.

    Also effectively stops the background fulfilment task (it will
    find the order missing and exit gracefully).

    **TMF622 spec reference:** DELETE /productOrder/{id}
    """
    record = product_orders.pop(order_id, None)
    if not record:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "ERR_NOT_FOUND",
                "reason": f"ProductOrder {order_id} not found",
                "@type": "Error",
            },
        )

    publish("ProductOrderDeleteEvent", {
        "productOrder": record,
    })

    return None
