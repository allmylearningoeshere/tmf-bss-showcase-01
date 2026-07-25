"""
TMF666 Account Management — BillingAccount resource.

Endpoints:
  POST   /accountManagement/v4/billingAccount          Create a billing account
  GET    /accountManagement/v4/billingAccount          List billing accounts
  GET    /accountManagement/v4/billingAccount/{id}     Retrieve a billing account
  PATCH  /accountManagement/v4/billingAccount/{id}     Update a billing account
  DELETE /accountManagement/v4/billingAccount/{id}     Delete a billing account

A BillingAccount ties a customer (TMF632 Individual) to their financial
relationship — currency, credit limit, bill structure, payment methods,
and running balance.  Creating an account after creating a party is
the second step in the BSS customer lifecycle.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from shared.store import billing_accounts
from shared.events import publish
from shared.schemas.tmf666 import (
    BillingAccount,
    BillingAccountCreate,
    BillingAccountUpdate,
)

router = APIRouter(
    prefix="/accountManagement/v4",
    tags=["TMF666 · Account Management"],
)

BASE_PATH = "/accountManagement/v4/billingAccount"

# Valid account states per TMF666
VALID_STATES = {"active", "suspended", "closed", "pending"}


# ---------------------------------------------------------------------------
# POST — create
# ---------------------------------------------------------------------------

@router.post(
    "/billingAccount",
    response_model=BillingAccount,
    status_code=201,
    summary="Create a billing account",
    response_description="Billing account created",
)
def create_billing_account(body: BillingAccountCreate) -> JSONResponse:
    """
    Creates a new BillingAccount.

    A billing account ties a customer (party) to their financial
    relationship.  Link it to an existing Individual via `relatedParty`.

    The server generates `id`, `href`, `state` (defaults to `active`),
    and an initial zero-balance entry.

    **TMF666 spec reference:** POST /billingAccount
    """
    account_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    record = {
        "id": account_id,
        "href": f"{BASE_PATH}/{account_id}",
        "state": body.state or "active",
        "createdAt": now,
        "lastUpdatedAt": now,
        "@type": "BillingAccount",
        "@baseType": "Account",
        "accountBalance": [
            {
                "balanceType": "currentBalance",
                "amount": {
                    "unit": body.currency or "EUR",
                    "value": 0.00,
                },
            },
        ],
        **body.model_dump(by_alias=True, exclude_none=True),
    }

    billing_accounts[account_id] = record

    publish("BillingAccountCreateEvent", {
        "billingAccount": record,
    })

    return JSONResponse(content=record, status_code=201)


# ---------------------------------------------------------------------------
# GET — list
# ---------------------------------------------------------------------------

@router.get(
    "/billingAccount",
    response_model=list[BillingAccount],
    summary="List billing accounts",
    response_description="Array of billing accounts",
)
def list_billing_accounts(
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=200, description="Page size"),
    name: str | None = Query(
        None,
        description="Filter by name (case-insensitive substring)",
    ),
    state: str | None = Query(
        None,
        description="Filter by state (active, suspended, closed, pending)",
    ),
    account_type: str | None = Query(
        None,
        alias="accountType",
        description="Filter by account type (individual, business)",
    ),
) -> JSONResponse:
    """
    Returns a paginated list of all BillingAccounts.

    Supports optional filtering by `name`, `state`, and `accountType`.

    **TMF666 spec reference:** GET /billingAccount
    """
    results = list(billing_accounts.values())

    if name:
        needle = name.lower()
        results = [r for r in results if needle in r.get("name", "").lower()]

    if state:
        results = [r for r in results if r.get("state") == state]

    if account_type:
        results = [r for r in results if r.get("accountType") == account_type]

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
    "/billingAccount/{account_id}",
    response_model=BillingAccount,
    summary="Retrieve a billing account",
    response_description="The requested billing account",
)
def get_billing_account(account_id: str) -> JSONResponse:
    """
    Returns a single BillingAccount by its ID, including current balance,
    bill structure, and linked party references.

    **TMF666 spec reference:** GET /billingAccount/{id}
    """
    record = billing_accounts.get(account_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "ERR_NOT_FOUND",
                "reason": f"BillingAccount {account_id} not found",
                "@type": "Error",
            },
        )
    return JSONResponse(content=record)


# ---------------------------------------------------------------------------
# PATCH — partial update
# ---------------------------------------------------------------------------

@router.patch(
    "/billingAccount/{account_id}",
    response_model=BillingAccount,
    summary="Update a billing account",
    response_description="Updated billing account",
)
def patch_billing_account(account_id: str, body: BillingAccountUpdate) -> JSONResponse:
    """
    Partially updates an existing BillingAccount.

    Common operations:
    - Change `state` to `suspended` or `closed`
    - Update `creditLimit`
    - Modify `billStructure` (cycle, format, delivery)
    - Add or change `paymentMethod`

    State transitions: `active → suspended → active`, `active → closed`,
    `suspended → closed`.  Reopening a closed account is not allowed.

    **TMF666 spec reference:** PATCH /billingAccount/{id}
    """
    record = billing_accounts.get(account_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "ERR_NOT_FOUND",
                "reason": f"BillingAccount {account_id} not found",
                "@type": "Error",
            },
        )

    updates = body.model_dump(by_alias=True, exclude_none=True)
    now = datetime.now(timezone.utc).isoformat()

    # Validate state transitions
    new_state = updates.get("state")
    if new_state:
        if new_state not in VALID_STATES:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "ERR_INVALID_STATE",
                    "reason": f"Invalid state '{new_state}'. Valid: {', '.join(sorted(VALID_STATES))}",
                    "@type": "Error",
                },
            )

        current_state = record.get("state")
        if current_state == "closed":
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "ERR_STATE_CONFLICT",
                    "reason": "Cannot modify a closed account",
                    "@type": "Error",
                },
            )

        if new_state == "closed":
            record["closedDate"] = now

    previous_state = record.get("state")
    record.update(updates)
    record["lastUpdatedAt"] = now

    event_type = (
        "BillingAccountStateChangeEvent"
        if new_state and new_state != previous_state
        else "BillingAccountAttributeValueChangeEvent"
    )

    publish(event_type, {
        "billingAccount": record,
    })

    return JSONResponse(content=record)


# ---------------------------------------------------------------------------
# DELETE — remove
# ---------------------------------------------------------------------------

@router.delete(
    "/billingAccount/{account_id}",
    status_code=204,
    summary="Delete a billing account",
    response_description="Billing account deleted (no content)",
)
def delete_billing_account(account_id: str):
    """
    Removes a BillingAccount from the store.

    Returns `204 No Content` on success.

    **TMF666 spec reference:** DELETE /billingAccount/{id}
    """
    record = billing_accounts.pop(account_id, None)
    if not record:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "ERR_NOT_FOUND",
                "reason": f"BillingAccount {account_id} not found",
                "@type": "Error",
            },
        )

    publish("BillingAccountDeleteEvent", {
        "billingAccount": record,
    })

    return None
