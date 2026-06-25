"""
TMF632 Party Management — Individual resource.

Endpoints:
  POST   /party/v5/individual          Create an individual
  GET    /party/v5/individual          List all individuals
  GET    /party/v5/individual/{id}     Retrieve one individual
  PATCH  /party/v5/individual/{id}     Partially update an individual
  DELETE /party/v5/individual/{id}     Delete an individual

All data lives in the shared in-memory store.  Every create / update /
delete publishes a TMF688-style event to the internal event bus.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from shared.store import individuals
from shared.events import publish
from shared.schemas.tmf632 import (
    Individual,
    IndividualCreate,
    IndividualUpdate,
)

router = APIRouter(
    prefix="/party/v5",
    tags=["TMF632 · Party Management"],
)

BASE_PATH = "/party/v5/individual"


# ---------------------------------------------------------------------------
# POST — create
# ---------------------------------------------------------------------------

@router.post(
    "/individual",
    response_model=Individual,
    status_code=201,
    summary="Create an individual",
    response_description="Individual created",
)
def create_individual(body: IndividualCreate) -> JSONResponse:
    """
    Creates a new Individual party.

    The server generates `id`, `href`, `status`, and `@type` / `@baseType`.
    Only `fullName` is required in the request body.

    **TMF632 spec reference:** POST /individual
    """
    individual_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    record = {
        "id": individual_id,
        "href": f"{BASE_PATH}/{individual_id}",
        "status": "initialized",
        "@type": "Individual",
        "@baseType": "Party",
        "createdAt": now,
        "lastUpdatedAt": now,
        **body.model_dump(by_alias=True, exclude_none=True),
    }

    individuals[individual_id] = record

    publish("IndividualCreateEvent", {
        "individual": record,
    })

    return JSONResponse(content=record, status_code=201)


# ---------------------------------------------------------------------------
# GET — list
# ---------------------------------------------------------------------------

@router.get(
    "/individual",
    response_model=list[Individual],
    summary="List individuals",
    response_description="Array of individuals",
)
def list_individuals(
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=200, description="Page size"),
    full_name: str | None = Query(
        None,
        alias="fullName",
        description="Filter by fullName (case-insensitive substring match)",
    ),
    status: str | None = Query(
        None,
        description="Filter by status (exact match)",
    ),
) -> JSONResponse:
    """
    Returns a paginated list of all Individual parties.

    Supports optional filtering by `fullName` (substring) and `status` (exact).
    Pagination via `offset` and `limit` query parameters.

    **TMF632 spec reference:** GET /individual
    """
    results = list(individuals.values())

    if full_name:
        needle = full_name.lower()
        results = [
            r for r in results
            if needle in r.get("fullName", "").lower()
        ]

    if status:
        results = [r for r in results if r.get("status") == status]

    total = len(results)
    page = results[offset: offset + limit]

    return JSONResponse(
        content=page,
        headers={
            "X-Total-Count": str(total),
            "X-Result-Count": str(len(page)),
        },
    )


# ---------------------------------------------------------------------------
# GET — retrieve by id
# ---------------------------------------------------------------------------

@router.get(
    "/individual/{individual_id}",
    response_model=Individual,
    summary="Retrieve an individual",
    response_description="The requested individual",
)
def get_individual(individual_id: str) -> JSONResponse:
    """
    Returns a single Individual party by its unique `id`.

    **TMF632 spec reference:** GET /individual/{id}
    """
    record = individuals.get(individual_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "ERR_NOT_FOUND",
                "reason": f"Individual {individual_id} not found",
                "@type": "Error",
            },
        )
    return JSONResponse(content=record)


# ---------------------------------------------------------------------------
# PATCH — partial update
# ---------------------------------------------------------------------------

@router.patch(
    "/individual/{individual_id}",
    response_model=Individual,
    summary="Partially update an individual",
    response_description="Updated individual",
)
def patch_individual(individual_id: str, body: IndividualUpdate) -> JSONResponse:
    """
    Merges the supplied fields into an existing Individual.
    Only the fields present in the request body are updated; all others
    remain unchanged.

    **TMF632 spec reference:** PATCH /individual/{id}
    """
    record = individuals.get(individual_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "ERR_NOT_FOUND",
                "reason": f"Individual {individual_id} not found",
                "@type": "Error",
            },
        )

    updates = body.model_dump(by_alias=True, exclude_none=True)
    record.update(updates)
    record["lastUpdatedAt"] = datetime.now(timezone.utc).isoformat()

    publish("IndividualAttributeValueChangeEvent", {
        "individual": record,
    })

    return JSONResponse(content=record)


# ---------------------------------------------------------------------------
# DELETE — remove
# ---------------------------------------------------------------------------

@router.delete(
    "/individual/{individual_id}",
    status_code=204,
    summary="Delete an individual",
    response_description="Individual deleted (no content)",
)
def delete_individual(individual_id: str):
    """
    Removes an Individual party from the store.

    Returns `204 No Content` on success.

    **TMF632 spec reference:** DELETE /individual/{id}
    """
    record = individuals.pop(individual_id, None)
    if not record:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "ERR_NOT_FOUND",
                "reason": f"Individual {individual_id} not found",
                "@type": "Error",
            },
        )

    publish("IndividualDeleteEvent", {
        "individual": record,
    })

    return None
