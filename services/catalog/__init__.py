"""
TMF620 Product Catalog Management.

Endpoints:
  POST   /productCatalog/v4/productSpecification          Create a spec
  GET    /productCatalog/v4/productSpecification          List specs
  GET    /productCatalog/v4/productSpecification/{id}     Retrieve a spec
  PATCH  /productCatalog/v4/productSpecification/{id}     Update a spec
  DELETE /productCatalog/v4/productSpecification/{id}     Delete a spec

  POST   /productCatalog/v4/productOffering               Create an offering
  GET    /productCatalog/v4/productOffering               List offerings
  GET    /productCatalog/v4/productOffering/{id}          Retrieve an offering
  PATCH  /productCatalog/v4/productOffering/{id}          Update an offering
  DELETE /productCatalog/v4/productOffering/{id}          Delete an offering

Seed data is loaded on import so the catalog is never empty.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from shared.store import product_specifications, product_offerings
from shared.events import publish
from shared.schemas.tmf620 import (
    ProductSpecification,
    ProductSpecificationCreate,
    ProductSpecificationUpdate,
    ProductOffering,
    ProductOfferingCreate,
    ProductOfferingUpdate,
)

# Load seed data on import
from services.catalog.seed import _seed  # noqa: F401

router = APIRouter(
    prefix="/productCatalog/v4",
    tags=["TMF620 · Product Catalog"],
)

SPEC_BASE = "/productCatalog/v4/productSpecification"
OFFERING_BASE = "/productCatalog/v4/productOffering"


# ===================================================================
# Product Specification endpoints
# ===================================================================

@router.post(
    "/productSpecification",
    response_model=ProductSpecification,
    status_code=201,
    summary="Create a product specification",
    response_description="Specification created",
)
def create_spec(body: ProductSpecificationCreate) -> JSONResponse:
    """
    Creates a new ProductSpecification — the technical blueprint for
    a product.  Specifications describe capabilities and characteristics
    that one or more ProductOfferings can reference.

    **TMF620 spec reference:** POST /productSpecification
    """
    spec_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    record = {
        "id": spec_id,
        "href": f"{SPEC_BASE}/{spec_id}",
        "@type": "ProductSpecification",
        "@baseType": "ProductSpecification",
        "lastUpdate": now,
        **body.model_dump(by_alias=True, exclude_none=True),
    }

    product_specifications[spec_id] = record

    publish("ProductSpecificationCreateEvent", {
        "productSpecification": record,
    })

    return JSONResponse(content=record, status_code=201)


@router.get(
    "/productSpecification",
    response_model=list[ProductSpecification],
    summary="List product specifications",
    response_description="Array of specifications",
)
def list_specs(
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=200, description="Page size"),
    name: str | None = Query(
        None,
        description="Filter by name (case-insensitive substring)",
    ),
    lifecycle_status: str | None = Query(
        None,
        alias="lifecycleStatus",
        description="Filter by lifecycle status (exact match)",
    ),
) -> JSONResponse:
    """
    Returns a paginated list of all ProductSpecifications.

    **TMF620 spec reference:** GET /productSpecification
    """
    results = list(product_specifications.values())

    if name:
        needle = name.lower()
        results = [r for r in results if needle in r.get("name", "").lower()]

    if lifecycle_status:
        results = [r for r in results if r.get("lifecycleStatus") == lifecycle_status]

    total = len(results)
    page = results[offset: offset + limit]

    return JSONResponse(
        content=page,
        headers={"X-Total-Count": str(total), "X-Result-Count": str(len(page))},
    )


@router.get(
    "/productSpecification/{spec_id}",
    response_model=ProductSpecification,
    summary="Retrieve a product specification",
    response_description="The requested specification",
)
def get_spec(spec_id: str) -> JSONResponse:
    """
    Returns a single ProductSpecification by its ID.

    **TMF620 spec reference:** GET /productSpecification/{id}
    """
    record = product_specifications.get(spec_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "ERR_NOT_FOUND",
                "reason": f"ProductSpecification {spec_id} not found",
                "@type": "Error",
            },
        )
    return JSONResponse(content=record)


@router.patch(
    "/productSpecification/{spec_id}",
    response_model=ProductSpecification,
    summary="Update a product specification",
    response_description="Updated specification",
)
def patch_spec(spec_id: str, body: ProductSpecificationUpdate) -> JSONResponse:
    """
    Partially updates an existing ProductSpecification.
    Only supplied fields are merged.

    **TMF620 spec reference:** PATCH /productSpecification/{id}
    """
    record = product_specifications.get(spec_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "ERR_NOT_FOUND",
                "reason": f"ProductSpecification {spec_id} not found",
                "@type": "Error",
            },
        )

    updates = body.model_dump(by_alias=True, exclude_none=True)
    record.update(updates)
    record["lastUpdate"] = datetime.now(timezone.utc).isoformat()

    publish("ProductSpecificationAttributeValueChangeEvent", {
        "productSpecification": record,
    })

    return JSONResponse(content=record)


@router.delete(
    "/productSpecification/{spec_id}",
    status_code=204,
    summary="Delete a product specification",
    response_description="Specification deleted (no content)",
)
def delete_spec(spec_id: str):
    """
    Removes a ProductSpecification from the catalog.

    **TMF620 spec reference:** DELETE /productSpecification/{id}
    """
    record = product_specifications.pop(spec_id, None)
    if not record:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "ERR_NOT_FOUND",
                "reason": f"ProductSpecification {spec_id} not found",
                "@type": "Error",
            },
        )

    publish("ProductSpecificationDeleteEvent", {
        "productSpecification": record,
    })

    return None


# ===================================================================
# Product Offering endpoints
# ===================================================================

@router.post(
    "/productOffering",
    response_model=ProductOffering,
    status_code=201,
    summary="Create a product offering",
    response_description="Offering created",
)
def create_offering(body: ProductOfferingCreate) -> JSONResponse:
    """
    Creates a new ProductOffering — a sellable product based on a
    ProductSpecification, with associated pricing.

    **TMF620 spec reference:** POST /productOffering
    """
    offering_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    record = {
        "id": offering_id,
        "href": f"{OFFERING_BASE}/{offering_id}",
        "@type": "ProductOffering",
        "@baseType": "ProductOffering",
        "lastUpdate": now,
        **body.model_dump(by_alias=True, exclude_none=True),
    }

    product_offerings[offering_id] = record

    publish("ProductOfferingCreateEvent", {
        "productOffering": record,
    })

    return JSONResponse(content=record, status_code=201)


@router.get(
    "/productOffering",
    response_model=list[ProductOffering],
    summary="List product offerings",
    response_description="Array of offerings",
)
def list_offerings(
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=200, description="Page size"),
    name: str | None = Query(
        None,
        description="Filter by name (case-insensitive substring)",
    ),
    lifecycle_status: str | None = Query(
        None,
        alias="lifecycleStatus",
        description="Filter by lifecycle status (exact match)",
    ),
    is_bundle: bool | None = Query(
        None,
        alias="isBundle",
        description="Filter bundles (true) or standalone offerings (false)",
    ),
) -> JSONResponse:
    """
    Returns a paginated list of all ProductOfferings.

    Supports filtering by name, lifecycle status, and bundle flag.

    **TMF620 spec reference:** GET /productOffering
    """
    results = list(product_offerings.values())

    if name:
        needle = name.lower()
        results = [r for r in results if needle in r.get("name", "").lower()]

    if lifecycle_status:
        results = [r for r in results if r.get("lifecycleStatus") == lifecycle_status]

    if is_bundle is not None:
        results = [r for r in results if r.get("isBundle") == is_bundle]

    total = len(results)
    page = results[offset: offset + limit]

    return JSONResponse(
        content=page,
        headers={"X-Total-Count": str(total), "X-Result-Count": str(len(page))},
    )


@router.get(
    "/productOffering/{offering_id}",
    response_model=ProductOffering,
    summary="Retrieve a product offering",
    response_description="The requested offering",
)
def get_offering(offering_id: str) -> JSONResponse:
    """
    Returns a single ProductOffering by its ID, including its linked
    ProductSpecification and pricing references.

    **TMF620 spec reference:** GET /productOffering/{id}
    """
    record = product_offerings.get(offering_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "ERR_NOT_FOUND",
                "reason": f"ProductOffering {offering_id} not found",
                "@type": "Error",
            },
        )
    return JSONResponse(content=record)


@router.patch(
    "/productOffering/{offering_id}",
    response_model=ProductOffering,
    summary="Update a product offering",
    response_description="Updated offering",
)
def patch_offering(offering_id: str, body: ProductOfferingUpdate) -> JSONResponse:
    """
    Partially updates an existing ProductOffering.
    Only supplied fields are merged.

    **TMF620 spec reference:** PATCH /productOffering/{id}
    """
    record = product_offerings.get(offering_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "ERR_NOT_FOUND",
                "reason": f"ProductOffering {offering_id} not found",
                "@type": "Error",
            },
        )

    updates = body.model_dump(by_alias=True, exclude_none=True)
    record.update(updates)
    record["lastUpdate"] = datetime.now(timezone.utc).isoformat()

    publish("ProductOfferingAttributeValueChangeEvent", {
        "productOffering": record,
    })

    return JSONResponse(content=record)


@router.delete(
    "/productOffering/{offering_id}",
    status_code=204,
    summary="Delete a product offering",
    response_description="Offering deleted (no content)",
)
def delete_offering(offering_id: str):
    """
    Removes a ProductOffering from the catalog.

    **TMF620 spec reference:** DELETE /productOffering/{id}
    """
    record = product_offerings.pop(offering_id, None)
    if not record:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "ERR_NOT_FOUND",
                "reason": f"ProductOffering {offering_id} not found",
                "@type": "Error",
            },
        )

    publish("ProductOfferingDeleteEvent", {
        "productOffering": record,
    })

    return None
