"""
Address Lookup — a thin proxy over the OpenPLZ API.

Endpoints:
  GET /addressLookup/v1/streets?postalCode=10115   List streets in a postcode

OpenPLZ (https://www.openplzapi.org) is a free, keyless public directory of
German streets and postal codes derived from OpenStreetMap. This router proxies
to it so the browser never talks to a third party directly — the frontend calls
our backend, our backend calls OpenPLZ, and we normalise the response into a
compact shape the Odyssey storefront can drop straight into its address fields.

This keeps the storefront clean, sidesteps CORS, and adds one more integration
endpoint to the stack without introducing any secrets.
"""

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from shared.events import publish

router = APIRouter(
    prefix="/addressLookup/v1",
    tags=["Address Lookup (OpenPLZ proxy)"],
)

OPENPLZ_BASE = "https://openplzapi.org"
REQUEST_TIMEOUT = 10.0  # seconds — OpenPLZ can be slow on a cold call


# ---------------------------------------------------------------------------
# GET — streets by postcode
# ---------------------------------------------------------------------------

@router.get(
    "/streets",
    summary="List streets in a German postcode",
    response_description="Normalised list of streets with locality",
)
async def lookup_streets(
    postal_code: str = Query(
        ...,
        alias="postalCode",
        min_length=5,
        max_length=5,
        pattern=r"^\d{5}$",
        description="A 5-digit German postcode, e.g. 10115",
    ),
) -> JSONResponse:
    """
    Returns every street registered in the given postcode, along with its
    locality (city) and borough where available.

    Proxies to OpenPLZ `GET /de/Streets?postalCode={code}` and reshapes the
    result into `{ street, postalCode, city, borough }` objects.
    """
    url = f"{OPENPLZ_BASE}/de/Streets"
    params = {"postalCode": postal_code, "page": 1, "pageSize": 50}

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.get(
                url, params=params, headers={"accept": "application/json"}
            )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail={
                "code": "ERR_UPSTREAM_TIMEOUT",
                "reason": "The address service did not respond in time.",
                "@type": "Error",
            },
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail={
                "code": "ERR_UPSTREAM_UNAVAILABLE",
                "reason": "The address service could not be reached.",
                "@type": "Error",
            },
        )

    if resp.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail={
                "code": "ERR_UPSTREAM_ERROR",
                "reason": f"Address service returned status {resp.status_code}.",
                "@type": "Error",
            },
        )

    raw = resp.json()
    results = [_normalise(item) for item in raw]

    publish("AddressLookupEvent", {
        "postalCode": postal_code,
        "resultCount": len(results),
    })

    return JSONResponse(
        content={"postalCode": postal_code, "results": results},
        headers={"X-Result-Count": str(len(results))},
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalise(item: dict) -> dict:
    """
    Reshape an OpenPLZ street record into the compact form the frontend uses.

    OpenPLZ returns objects like:
        {
          "name": "Grabbeallee",
          "postalCode": "13156",
          "locality": "Berlin",
          "borough": "Pankow",
          "federalState": { "name": "Berlin" }, ...
        }
    """
    federal_state = item.get("federalState") or {}
    return {
        "street": item.get("name", ""),
        "postalCode": item.get("postalCode", ""),
        "city": item.get("locality", ""),
        "borough": item.get("borough") or "",
        "federalState": federal_state.get("name", "") if isinstance(federal_state, dict) else "",
    }
