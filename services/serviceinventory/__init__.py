"""TMF638 Service Inventory — CRUD endpoints."""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from shared.store import services
from shared.events import publish
from shared.schemas.tmf638 import Service, ServiceCreate, ServiceUpdate

router = APIRouter(prefix="/serviceInventory/v4", tags=["TMF638 · Service Inventory"])
BASE_PATH = "/serviceInventory/v4/service"

@router.post("/service", response_model=Service, status_code=201, summary="Create a service instance")
def create_service(body: ServiceCreate) -> JSONResponse:
    """Create a Service in inventory. Auto-created during provisioning stage.

    **TMF638 spec reference:** POST /service"""
    sid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    record = {
        "id": sid, "href": f"{BASE_PATH}/{sid}", "state": "active",
        "startDate": now, "endDate": None,
        "createdAt": now, "lastUpdatedAt": now,
        "@type": "Service", "@baseType": "Service",
        **body.model_dump(by_alias=True, exclude_none=True),
    }
    services[sid] = record
    publish("ServiceCreateEvent", {"service": record})
    return JSONResponse(content=record, status_code=201)

@router.get("/service", response_model=list[Service], summary="List services")
def list_services(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                  state: str | None = None, name: str | None = None) -> JSONResponse:
    """List all service instances. **TMF638:** GET /service"""
    results = list(services.values())
    if state:
        results = [r for r in results if r.get("state") == state]
    if name:
        needle = name.lower()
        results = [r for r in results if needle in r.get("name", "").lower()]
    total = len(results)
    return JSONResponse(content=results[offset:offset+limit],
                        headers={"X-Total-Count": str(total), "X-Result-Count": str(min(limit, total-offset))})

@router.get("/service/{service_id}", response_model=Service, summary="Retrieve a service")
def get_service(service_id: str) -> JSONResponse:
    """Get a service with its characteristics (MSISDN, IMSI, etc.). **TMF638:** GET /service/{id}"""
    record = services.get(service_id)
    if not record:
        raise HTTPException(404, detail={"code": "ERR_NOT_FOUND", "reason": f"Service {service_id} not found", "@type": "Error"})
    return JSONResponse(content=record)

@router.patch("/service/{service_id}", response_model=Service, summary="Update a service")
def patch_service(service_id: str, body: ServiceUpdate) -> JSONResponse:
    """Update a service state or characteristics. **TMF638:** PATCH /service/{id}"""
    record = services.get(service_id)
    if not record:
        raise HTTPException(404, detail={"code": "ERR_NOT_FOUND", "reason": f"Service {service_id} not found", "@type": "Error"})
    updates = body.model_dump(by_alias=True, exclude_none=True)
    now = datetime.now(timezone.utc).isoformat()
    if updates.get("state") == "terminated":
        record["endDate"] = now
    record.update(updates)
    record["lastUpdatedAt"] = now
    services[service_id] = record
    publish("ServiceStateChangeEvent", {"service": {"id": record["id"], "state": record["state"]}})
    return JSONResponse(content=record)

@router.delete("/service/{service_id}", status_code=204, summary="Delete a service")
def delete_service(service_id: str):
    """Remove a service from inventory. **TMF638:** DELETE /service/{id}"""
    record = services.pop(service_id, None)
    if not record:
        raise HTTPException(404, detail={"code": "ERR_NOT_FOUND", "reason": f"Service {service_id} not found", "@type": "Error"})
    publish("ServiceDeleteEvent", {"service": record})
    return None
