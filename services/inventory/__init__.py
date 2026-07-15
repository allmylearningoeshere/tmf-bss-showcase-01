"""
TMF637 Product Inventory.

Endpoints:
  POST   /productInventory/v4/product          Create a product instance
  GET    /productInventory/v4/product          List product instances
  GET    /productInventory/v4/product/{id}     Retrieve a product instance
  PATCH  /productInventory/v4/product/{id}     Update a product instance
  DELETE /productInventory/v4/product/{id}     Delete a product instance

A Product in inventory represents what a customer actually has —
active subscriptions, installed services, provisioned lines.

Products are auto-created when an order reaches the `completed` state
(see services/order).  They can also be created manually for data
migrations or bulk imports.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from shared.store import product_inventory
from shared.events import publish
from shared.schemas.tmf637 import (
    Product,
    ProductCreate,
    ProductUpdate,
)

router = APIRouter(
    prefix="/productInventory/v4",
    tags=["TMF637 · Product Inventory"],
)

BASE_PATH = "/productInventory/v4/product"

VALID_STATUSES = {"created", "active", "suspended", "pendingTerminate", "terminated"}


# ---------------------------------------------------------------------------
# POST — create
# ---------------------------------------------------------------------------

@router.post(
    "/product",
    response_model=Product,
    status_code=201,
    summary="Create a product instance",
    response_description="Product instance created",
)
def create_product(body: ProductCreate) -> JSONResponse:
    """
    Creates a new Product instance in inventory.

    Usually auto-created by the order fulfilment state machine when
    an order reaches `completed`.  Can also be called directly for
    data migration or manual provisioning.

    **TMF637 spec reference:** POST /product
    """
    product_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    record = {
        "id": product_id,
        "href": f"{BASE_PATH}/{product_id}",
        "status": body.status or "active",
        "startDate": now,
        "terminationDate": None,
        "createdAt": now,
        "lastUpdatedAt": now,
        "@type": "Product",
        "@baseType": "Product",
        **body.model_dump(by_alias=True, exclude_none=True),
    }

    product_inventory[product_id] = record

    publish("ProductCreateEvent", {
        "product": record,
    })

    return JSONResponse(content=record, status_code=201)


# ---------------------------------------------------------------------------
# GET — list
# ---------------------------------------------------------------------------

@router.get(
    "/product",
    response_model=list[Product],
    summary="List product instances",
    response_description="Array of product instances",
)
def list_products(
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=200, description="Page size"),
    status: str | None = Query(
        None,
        description="Filter by status (active, suspended, terminated)",
    ),
    name: str | None = Query(
        None,
        description="Filter by name (case-insensitive substring)",
    ),
    related_party_id: str | None = Query(
        None,
        alias="relatedParty.id",
        description="Filter by related party ID (the customer who owns it)",
    ),
) -> JSONResponse:
    """
    Returns a paginated list of all Product instances in inventory.

    Supports filtering by `status`, `name`, and `relatedParty.id`
    (to find all products belonging to a specific customer).

    **TMF637 spec reference:** GET /product
    """
    results = list(product_inventory.values())

    if status:
        results = [r for r in results if r.get("status") == status]

    if name:
        needle = name.lower()
        results = [r for r in results if needle in r.get("name", "").lower()]

    if related_party_id:
        filtered = []
        for r in results:
            for rp in r.get("relatedParty", []):
                if rp.get("id") == related_party_id:
                    filtered.append(r)
                    break
        results = filtered

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
    "/product/{product_id}",
    response_model=Product,
    summary="Retrieve a product instance",
    response_description="The requested product instance",
)
def get_product(product_id: str) -> JSONResponse:
    """
    Returns a single Product instance by ID, including its offering
    reference, characteristics, pricing, and linked order.

    **TMF637 spec reference:** GET /product/{id}
    """
    record = product_inventory.get(product_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "ERR_NOT_FOUND",
                "reason": f"Product {product_id} not found",
                "@type": "Error",
            },
        )
    return JSONResponse(content=record)


# ---------------------------------------------------------------------------
# PATCH — partial update
# ---------------------------------------------------------------------------

@router.patch(
    "/product/{product_id}",
    response_model=Product,
    summary="Update a product instance",
    response_description="Updated product instance",
)
def patch_product(product_id: str, body: ProductUpdate) -> JSONResponse:
    """
    Partially updates an existing Product instance.

    Common operations:
    - Suspend: set `status` to `suspended`
    - Terminate: set `status` to `terminated` (sets terminationDate)
    - Re-activate: set `status` back to `active`
    - Update characteristics (e.g. change speed tier)

    **TMF637 spec reference:** PATCH /product/{id}
    """
    record = product_inventory.get(product_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "ERR_NOT_FOUND",
                "reason": f"Product {product_id} not found",
                "@type": "Error",
            },
        )

    updates = body.model_dump(by_alias=True, exclude_none=True)
    now = datetime.now(timezone.utc).isoformat()

    new_status = updates.get("status")
    if new_status:
        if new_status not in VALID_STATUSES:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "ERR_INVALID_STATUS",
                    "reason": f"Invalid status '{new_status}'. Valid: {', '.join(sorted(VALID_STATUSES))}",
                    "@type": "Error",
                },
            )

        if new_status == "terminated":
            record["terminationDate"] = now

    current_status = record.get("status")
    record.update(updates)
    record["lastUpdatedAt"] = now

    event_type = (
        "ProductStatusChangeEvent"
        if new_status and new_status != current_status
        else "ProductAttributeValueChangeEvent"
    )

    publish(event_type, {
        "product": record,
    })

    return JSONResponse(content=record)


# ---------------------------------------------------------------------------
# DELETE — remove
# ---------------------------------------------------------------------------

@router.delete(
    "/product/{product_id}",
    status_code=204,
    summary="Delete a product instance",
    response_description="Product instance deleted (no content)",
)
def delete_product(product_id: str):
    """
    Removes a Product instance from inventory.

    **TMF637 spec reference:** DELETE /product/{id}
    """
    record = product_inventory.pop(product_id, None)
    if not record:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "ERR_NOT_FOUND",
                "reason": f"Product {product_id} not found",
                "@type": "Error",
            },
        )

    publish("ProductDeleteEvent", {
        "product": record,
    })

    return None
