"""TMF700 Shipment Tracking — CRUD endpoints."""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from shared.store import shipments
from shared.events import publish
from shared.schemas.tmf700 import Shipment, ShipmentCreate, ShipmentUpdate

router = APIRouter(prefix="/shipmentTracking/v1", tags=["TMF700 · Shipment Tracking"])
BASE_PATH = "/shipmentTracking/v1/shipment"
VALID_STATUSES = {"processing", "shipped", "inTransit", "delivered", "returned", "cancelled"}

@router.post("/shipment", response_model=Shipment, status_code=201, summary="Create a shipment")
def create_shipment(body: ShipmentCreate) -> JSONResponse:
    """Create a Shipment. Auto-created by order fulfilment for physical SIM orders.

    **TMF700 spec reference:** POST /shipment"""
    sid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    record = {
        "id": sid, "href": f"{BASE_PATH}/{sid}", "status": "processing",
        "statusHistory": [{"status": "processing", "timestamp": now}],
        "createdAt": now, "lastUpdatedAt": now,
        "@type": "Shipment", "@baseType": "Shipment",
        **body.model_dump(by_alias=True, exclude_none=True),
    }
    if not record.get("trackingNumber"):
        record["trackingNumber"] = f"TRK-{uuid.uuid4().hex[:10].upper()}"
    shipments[sid] = record
    publish("ShipmentCreateEvent", {"shipment": record})
    return JSONResponse(content=record, status_code=201)

@router.get("/shipment", response_model=list[Shipment], summary="List shipments")
def list_shipments(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                   status: str | None = None, order_id: str | None = Query(None, alias="orderId")) -> JSONResponse:
    """List all shipments with optional filtering. **TMF700:** GET /shipment"""
    results = list(shipments.values())
    if status:
        results = [r for r in results if r.get("status") == status]
    if order_id:
        results = [r for r in results if (r.get("productOrder") or {}).get("id") == order_id]
    total = len(results)
    return JSONResponse(content=results[offset:offset+limit],
                        headers={"X-Total-Count": str(total), "X-Result-Count": str(min(limit, total-offset))})

@router.get("/shipment/{shipment_id}", response_model=Shipment, summary="Retrieve a shipment")
def get_shipment(shipment_id: str) -> JSONResponse:
    """Get a shipment with full status history. **TMF700:** GET /shipment/{id}"""
    record = shipments.get(shipment_id)
    if not record:
        raise HTTPException(404, detail={"code": "ERR_NOT_FOUND", "reason": f"Shipment {shipment_id} not found", "@type": "Error"})
    return JSONResponse(content=record)

@router.patch("/shipment/{shipment_id}", response_model=Shipment, summary="Update a shipment")
def patch_shipment(shipment_id: str, body: ShipmentUpdate) -> JSONResponse:
    """Update shipment status. Each transition is recorded in statusHistory. **TMF700:** PATCH /shipment/{id}"""
    record = shipments.get(shipment_id)
    if not record:
        raise HTTPException(404, detail={"code": "ERR_NOT_FOUND", "reason": f"Shipment {shipment_id} not found", "@type": "Error"})
    updates = body.model_dump(by_alias=True, exclude_none=True)
    now = datetime.now(timezone.utc).isoformat()
    new_status = updates.get("status")
    if new_status:
        if new_status not in VALID_STATUSES:
            raise HTTPException(400, detail={"code": "ERR_INVALID_STATUS", "reason": f"Invalid status '{new_status}'", "@type": "Error"})
        history = record.get("statusHistory") or []
        history.append({"status": new_status, "timestamp": now})
        record["statusHistory"] = history
    record.update(updates)
    record["lastUpdatedAt"] = now
    shipments[shipment_id] = record
    publish("ShipmentStatusChangeEvent", {"shipment": {"id": record["id"], "status": record["status"]}})
    return JSONResponse(content=record)

@router.delete("/shipment/{shipment_id}", status_code=204, summary="Delete a shipment")
def delete_shipment(shipment_id: str):
    """Remove a shipment. **TMF700:** DELETE /shipment/{id}"""
    record = shipments.pop(shipment_id, None)
    if not record:
        raise HTTPException(404, detail={"code": "ERR_NOT_FOUND", "reason": f"Shipment {shipment_id} not found", "@type": "Error"})
    publish("ShipmentDeleteEvent", {"shipment": record})
    return None
