"""TMF641 Service Order Management — CRUD endpoints."""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from shared.store import service_orders
from shared.events import publish
from shared.schemas.tmf641 import ServiceOrder, ServiceOrderCreate, ServiceOrderUpdate

router = APIRouter(prefix="/serviceOrderingManagement/v4", tags=["TMF641 · Service Ordering"])
BASE_PATH = "/serviceOrderingManagement/v4/serviceOrder"

@router.post("/serviceOrder", response_model=ServiceOrder, status_code=201, summary="Create a service order")
def create_service_order(body: ServiceOrderCreate) -> JSONResponse:
    """Create a ServiceOrder to trigger network provisioning. Auto-created during order fulfilment.

    **TMF641 spec reference:** POST /serviceOrder"""
    sid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    record = {
        "id": sid, "href": f"{BASE_PATH}/{sid}", "state": "acknowledged",
        "orderDate": now, "completionDate": None,
        "createdAt": now, "lastUpdatedAt": now,
        "@type": "ServiceOrder", "@baseType": "ServiceOrder",
        **body.model_dump(by_alias=True, exclude_none=True),
    }
    service_orders[sid] = record
    publish("ServiceOrderCreateEvent", {"serviceOrder": record})
    return JSONResponse(content=record, status_code=201)

@router.get("/serviceOrder", response_model=list[ServiceOrder], summary="List service orders")
def list_service_orders(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                        state: str | None = None) -> JSONResponse:
    """List all service orders. **TMF641:** GET /serviceOrder"""
    results = list(service_orders.values())
    if state:
        results = [r for r in results if r.get("state") == state]
    total = len(results)
    return JSONResponse(content=results[offset:offset+limit],
                        headers={"X-Total-Count": str(total), "X-Result-Count": str(min(limit, total-offset))})

@router.get("/serviceOrder/{so_id}", response_model=ServiceOrder, summary="Retrieve a service order")
def get_service_order(so_id: str) -> JSONResponse:
    """Get a service order. **TMF641:** GET /serviceOrder/{id}"""
    record = service_orders.get(so_id)
    if not record:
        raise HTTPException(404, detail={"code": "ERR_NOT_FOUND", "reason": f"ServiceOrder {so_id} not found", "@type": "Error"})
    return JSONResponse(content=record)

@router.patch("/serviceOrder/{so_id}", response_model=ServiceOrder, summary="Update a service order")
def patch_service_order(so_id: str, body: ServiceOrderUpdate) -> JSONResponse:
    """Update a service order state. **TMF641:** PATCH /serviceOrder/{id}"""
    record = service_orders.get(so_id)
    if not record:
        raise HTTPException(404, detail={"code": "ERR_NOT_FOUND", "reason": f"ServiceOrder {so_id} not found", "@type": "Error"})
    updates = body.model_dump(by_alias=True, exclude_none=True)
    now = datetime.now(timezone.utc).isoformat()
    record.update(updates)
    record["lastUpdatedAt"] = now
    if updates.get("state") == "completed":
        record["completionDate"] = now
    service_orders[so_id] = record
    publish("ServiceOrderStateChangeEvent", {"serviceOrder": {"id": record["id"], "state": record["state"]}})
    return JSONResponse(content=record)

@router.delete("/serviceOrder/{so_id}", status_code=204, summary="Delete a service order")
def delete_service_order(so_id: str):
    """Remove a service order. **TMF641:** DELETE /serviceOrder/{id}"""
    record = service_orders.pop(so_id, None)
    if not record:
        raise HTTPException(404, detail={"code": "ERR_NOT_FOUND", "reason": f"ServiceOrder {so_id} not found", "@type": "Error"})
    publish("ServiceOrderDeleteEvent", {"serviceOrder": record})
    return None
