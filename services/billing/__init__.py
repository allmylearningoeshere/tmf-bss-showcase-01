"""TMF678 Customer Bill Management — CRUD endpoints."""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from shared.store import customer_bills
from shared.events import publish
from shared.schemas.tmf678 import CustomerBill, CustomerBillCreate, CustomerBillUpdate

router = APIRouter(prefix="/customerBillManagement/v4", tags=["TMF678 · Customer Bill"])
BASE_PATH = "/customerBillManagement/v4/customerBill"

@router.post("/customerBill", response_model=CustomerBill, status_code=201, summary="Create a customer bill")
def create_customer_bill(body: CustomerBillCreate) -> JSONResponse:
    """Create a CustomerBill. Auto-created during the billing stage of order fulfilment.

    **TMF678 spec reference:** POST /customerBill"""
    bid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    record = {
        "id": bid, "href": f"{BASE_PATH}/{bid}", "state": "new",
        "runType": "onCycle",
        "createdAt": now, "lastUpdatedAt": now,
        "@type": "CustomerBill", "@baseType": "CustomerBill",
        **body.model_dump(by_alias=True, exclude_none=True),
    }
    customer_bills[bid] = record
    publish("CustomerBillCreateEvent", {"customerBill": record})
    return JSONResponse(content=record, status_code=201)

@router.get("/customerBill", response_model=list[CustomerBill], summary="List customer bills")
def list_customer_bills(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                        state: str | None = None,
                        billing_account_id: str | None = Query(None, alias="billingAccount.id")) -> JSONResponse:
    """List all bills with optional filtering. **TMF678:** GET /customerBill"""
    results = list(customer_bills.values())
    if state:
        results = [r for r in results if r.get("state") == state]
    if billing_account_id:
        results = [r for r in results if (r.get("billingAccount") or {}).get("id") == billing_account_id]
    total = len(results)
    return JSONResponse(content=results[offset:offset+limit],
                        headers={"X-Total-Count": str(total), "X-Result-Count": str(min(limit, total-offset))})

@router.get("/customerBill/{bill_id}", response_model=CustomerBill, summary="Retrieve a customer bill")
def get_customer_bill(bill_id: str) -> JSONResponse:
    """Get a bill with line items and amounts. **TMF678:** GET /customerBill/{id}"""
    record = customer_bills.get(bill_id)
    if not record:
        raise HTTPException(404, detail={"code": "ERR_NOT_FOUND", "reason": f"CustomerBill {bill_id} not found", "@type": "Error"})
    return JSONResponse(content=record)

@router.patch("/customerBill/{bill_id}", response_model=CustomerBill, summary="Update a customer bill")
def patch_customer_bill(bill_id: str, body: CustomerBillUpdate) -> JSONResponse:
    """Update bill state or apply payments. **TMF678:** PATCH /customerBill/{id}"""
    record = customer_bills.get(bill_id)
    if not record:
        raise HTTPException(404, detail={"code": "ERR_NOT_FOUND", "reason": f"CustomerBill {bill_id} not found", "@type": "Error"})
    updates = body.model_dump(by_alias=True, exclude_none=True)
    now = datetime.now(timezone.utc).isoformat()
    record.update(updates)
    record["lastUpdatedAt"] = now
    customer_bills[bill_id] = record
    publish("CustomerBillStateChangeEvent", {"customerBill": {"id": record["id"], "state": record["state"]}})
    return JSONResponse(content=record)

@router.delete("/customerBill/{bill_id}", status_code=204, summary="Delete a customer bill")
def delete_customer_bill(bill_id: str):
    """Remove a bill. **TMF678:** DELETE /customerBill/{id}"""
    record = customer_bills.pop(bill_id, None)
    if not record:
        raise HTTPException(404, detail={"code": "ERR_NOT_FOUND", "reason": f"CustomerBill {bill_id} not found", "@type": "Error"})
    publish("CustomerBillDeleteEvent", {"customerBill": record})
    return None
