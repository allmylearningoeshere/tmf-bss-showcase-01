"""
TMF629 Customer Management.

Endpoints:
  POST   /customerManagement/v4/customer          Create a customer
  GET    /customerManagement/v4/customer          List customers
  GET    /customerManagement/v4/customer/{id}     Retrieve a customer
  PATCH  /customerManagement/v4/customer/{id}     Update a customer
  DELETE /customerManagement/v4/customer/{id}     Delete a customer

A Customer is a Party (TMF632) that has entered into a commercial
relationship.  Creating a Customer is the step between "we know who
this person is" and "they can now buy from us and be billed".
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from shared.store import customers
from shared.events import publish
from shared.schemas.tmf629 import (
    Customer,
    CustomerCreate,
    CustomerUpdate,
)

router = APIRouter(
    prefix="/customerManagement/v4",
    tags=["TMF629 · Customer Management"],
)

BASE_PATH = "/customerManagement/v4/customer"

VALID_STATUSES = {"approved", "pending", "suspended", "closed"}


# ---------------------------------------------------------------------------
# POST — create
# ---------------------------------------------------------------------------

@router.post(
    "/customer",
    response_model=Customer,
    status_code=201,
    summary="Create a customer",
    response_description="Customer created",
)
def create_customer(body: CustomerCreate) -> JSONResponse:
    """
    Creates a new Customer by linking an existing Party (Individual or
    Organisation) to a commercial relationship.

    The `engagedParty` field must reference an existing Individual
    created via TMF632.  Optionally link billing accounts via the
    `account` array.

    **TMF629 spec reference:** POST /customer
    """
    customer_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    record = {
        "id": customer_id,
        "href": f"{BASE_PATH}/{customer_id}",
        "status": body.status or "approved",
        "createdAt": now,
        "lastUpdatedAt": now,
        "@type": "Customer",
        "@baseType": "Customer",
        **body.model_dump(by_alias=True, exclude_none=True),
    }

    customers[customer_id] = record

    publish("CustomerCreateEvent", {
        "customer": record,
    })

    return JSONResponse(content=record, status_code=201)


# ---------------------------------------------------------------------------
# GET — list
# ---------------------------------------------------------------------------

@router.get(
    "/customer",
    response_model=list[Customer],
    summary="List customers",
    response_description="Array of customers",
)
def list_customers(
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=200, description="Page size"),
    name: str | None = Query(
        None,
        description="Filter by name (case-insensitive substring)",
    ),
    status: str | None = Query(
        None,
        description="Filter by status (approved, pending, suspended, closed)",
    ),
    customer_category: str | None = Query(
        None,
        alias="customerCategory",
        description="Filter by category (residential, business, wholesale)",
    ),
) -> JSONResponse:
    """
    Returns a paginated list of all Customers.

    **TMF629 spec reference:** GET /customer
    """
    results = list(customers.values())

    if name:
        needle = name.lower()
        results = [r for r in results if needle in r.get("name", "").lower()]

    if status:
        results = [r for r in results if r.get("status") == status]

    if customer_category:
        results = [r for r in results if r.get("customerCategory") == customer_category]

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
    "/customer/{customer_id}",
    response_model=Customer,
    summary="Retrieve a customer",
    response_description="The requested customer",
)
def get_customer(customer_id: str) -> JSONResponse:
    """
    Returns a single Customer by ID, including the engaged party,
    linked accounts, and credit profile.

    **TMF629 spec reference:** GET /customer/{id}
    """
    record = customers.get(customer_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "ERR_NOT_FOUND",
                "reason": f"Customer {customer_id} not found",
                "@type": "Error",
            },
        )
    return JSONResponse(content=record)


# ---------------------------------------------------------------------------
# PATCH — partial update
# ---------------------------------------------------------------------------

@router.patch(
    "/customer/{customer_id}",
    response_model=Customer,
    summary="Update a customer",
    response_description="Updated customer",
)
def patch_customer(customer_id: str, body: CustomerUpdate) -> JSONResponse:
    """
    Partially updates an existing Customer.

    Common operations: change status, update category or rank,
    link additional accounts, modify contact preferences.

    **TMF629 spec reference:** PATCH /customer/{id}
    """
    record = customers.get(customer_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "ERR_NOT_FOUND",
                "reason": f"Customer {customer_id} not found",
                "@type": "Error",
            },
        )

    updates = body.model_dump(by_alias=True, exclude_none=True)
    now = datetime.now(timezone.utc).isoformat()

    new_status = updates.get("status")
    if new_status and new_status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "ERR_INVALID_STATUS",
                "reason": f"Invalid status '{new_status}'. Valid: {', '.join(sorted(VALID_STATUSES))}",
                "@type": "Error",
            },
        )

    current_status = record.get("status")
    if current_status == "closed":
        raise HTTPException(
            status_code=409,
            detail={
                "code": "ERR_STATE_CONFLICT",
                "reason": "Cannot modify a closed customer",
                "@type": "Error",
            },
        )

    record.update(updates)
    record["lastUpdatedAt"] = now

    event_type = (
        "CustomerStateChangeEvent"
        if new_status and new_status != current_status
        else "CustomerAttributeValueChangeEvent"
    )

    publish(event_type, {
        "customer": record,
    })

    return JSONResponse(content=record)


# ---------------------------------------------------------------------------
# DELETE — remove
# ---------------------------------------------------------------------------

@router.delete(
    "/customer/{customer_id}",
    status_code=204,
    summary="Delete a customer",
    response_description="Customer deleted (no content)",
)
def delete_customer(customer_id: str):
    """
    Removes a Customer from the store.

    **TMF629 spec reference:** DELETE /customer/{id}
    """
    record = customers.pop(customer_id, None)
    if not record:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "ERR_NOT_FOUND",
                "reason": f"Customer {customer_id} not found",
                "@type": "Error",
            },
        )

    publish("CustomerDeleteEvent", {
        "customer": record,
    })

    return None
