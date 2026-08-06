"""
TMF622 Product Ordering Management.

Enhanced fulfilment state machine for Mobile SIM orders:

    acknowledged
      → shipping (physical SIM only)
          processing → shipped → delivered
      → provisioning
          service order created → service active in inventory
      → billing
          charges applied → customer bill created
      → completed
          product in inventory

eSIM orders skip the shipping stage entirely.
Each stage updates the order's milestone and milestoneHistory fields,
and creates persisted entities in the relevant TMF stores.
"""

import uuid
import asyncio
import random
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse

from shared.store import (
    product_orders, product_inventory, shipments,
    service_orders, services, customer_bills, billing_accounts,
)
from shared.events import publish
from shared.schemas.tmf622 import (
    ProductOrder, ProductOrderCreate, ProductOrderUpdate,
)

router = APIRouter(
    prefix="/productOrderingManagement/v4",
    tags=["TMF622 · Product Ordering"],
)

BASE_PATH = "/productOrderingManagement/v4/productOrder"

VALID_STATES = {
    "acknowledged", "inProgress", "completed", "cancelled",
    "partial", "failed", "held", "pending",
    "assessingCancellation", "pendingCancellation",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _detect_sim_type(record: dict) -> str:
    """Detect SIM type from orderItem characteristics. Default: eSIM."""
    for item in record.get("orderItem", []):
        for char in item.get("productCharacteristic", []):
            if char.get("name", "").lower() == "simtype":
                return char.get("value", "eSIM")
    return "eSIM"


def _set_milestone(record: dict, milestone: str) -> None:
    """Update the current milestone and append to history."""
    now = datetime.now(timezone.utc).isoformat()
    record["milestone"] = milestone
    history = record.get("milestoneHistory") or []
    history.append({"milestone": milestone, "timestamp": now})
    record["milestoneHistory"] = history
    record["lastUpdatedAt"] = now


def _add_related_entity(record: dict, entity_id: str, entity_type: str, href: str) -> None:
    """Append a related entity reference to the order."""
    related = record.get("relatedEntity") or []
    related.append({"id": entity_id, "href": href, "@referredType": entity_type})
    record["relatedEntity"] = related


def _gen_msisdn() -> str:
    return f"+49{random.randint(151, 179)}{random.randint(1000000, 9999999)}"


def _gen_imsi() -> str:
    return f"26201{random.randint(1000000000, 9999999999)}"


def _gen_iccid() -> str:
    return f"8949{random.randint(10000000000000, 99999999999999)}"


# ---------------------------------------------------------------------------
# State machine — enhanced fulfilment flow
# ---------------------------------------------------------------------------

async def _advance_order(order_id: str) -> None:
    """
    Full post-submission fulfilment for Mobile SIM orders.

    Physical SIM: shipping → provisioning → billing → completed
    eSIM:         provisioning → billing → completed
    """
    await asyncio.sleep(2)

    record = product_orders.get(order_id)
    if not record or record.get("state") != "acknowledged":
        return

    now = datetime.now(timezone.utc).isoformat()
    sim_type = _detect_sim_type(record)
    record["state"] = "inProgress"
    record["simType"] = sim_type
    _set_milestone(record, "fulfilment.started")

    for item in record.get("orderItem", []):
        item["state"] = "inProgress"

    product_orders[order_id] = record
    publish("ProductOrderStateChangeEvent", {
        "productOrder": {"id": order_id, "state": "inProgress", "previousState": "acknowledged", "simType": sim_type},
    })

    # =================================================================
    # STAGE 1: SHIPPING (physical SIM only)
    # =================================================================
    if sim_type.lower() in ("physical", "physicalsim", "physical sim"):
        _set_milestone(record, "shipping.processing")
        product_orders[order_id] = record

        shipment_id = str(uuid.uuid4())
        shipment = {
            "id": shipment_id,
            "href": f"/shipmentTracking/v1/shipment/{shipment_id}",
            "status": "processing",
            "trackingNumber": f"TRK-{uuid.uuid4().hex[:10].upper()}",
            "carrier": "DHL Express",
            "description": f"SIM card shipment for order {order_id}",
            "statusHistory": [{"status": "processing", "timestamp": now}],
            "productOrder": {"id": order_id, "href": f"{BASE_PATH}/{order_id}", "@referredType": "ProductOrder"},
            "shipmentItem": [{"id": "1", "quantity": 1, "description": "Physical SIM card"}],
            "createdAt": now, "lastUpdatedAt": now,
            "@type": "Shipment", "@baseType": "Shipment",
        }
        shipments[shipment_id] = shipment
        _add_related_entity(record, shipment_id, "Shipment", shipment["href"])
        product_orders[order_id] = record
        publish("ShipmentCreateEvent", {"shipment": shipment})

        # shipped
        await asyncio.sleep(2)
        record = product_orders.get(order_id)
        if not record or record.get("state") == "cancelled":
            return
        now2 = datetime.now(timezone.utc).isoformat()
        shipment["status"] = "shipped"
        shipment["statusHistory"].append({"status": "shipped", "timestamp": now2})
        shipment["lastUpdatedAt"] = now2
        shipments[shipment_id] = shipment
        _set_milestone(record, "shipping.shipped")
        product_orders[order_id] = record
        publish("ShipmentStatusChangeEvent", {"shipment": {"id": shipment_id, "status": "shipped"}})

        # delivered
        await asyncio.sleep(2)
        record = product_orders.get(order_id)
        if not record or record.get("state") == "cancelled":
            return
        now3 = datetime.now(timezone.utc).isoformat()
        shipment["status"] = "delivered"
        shipment["statusHistory"].append({"status": "delivered", "timestamp": now3})
        shipment["lastUpdatedAt"] = now3
        shipments[shipment_id] = shipment
        _set_milestone(record, "shipping.delivered")
        product_orders[order_id] = record
        publish("ShipmentStatusChangeEvent", {"shipment": {"id": shipment_id, "status": "delivered"}})

    # =================================================================
    # STAGE 2: PROVISIONING
    # =================================================================
    record = product_orders.get(order_id)
    if not record or record.get("state") == "cancelled":
        return

    now = datetime.now(timezone.utc).isoformat()
    _set_milestone(record, "provisioning.inProgress")
    product_orders[order_id] = record

    # Create Service Order (TMF641)
    so_id = str(uuid.uuid4())
    service_order = {
        "id": so_id,
        "href": f"/serviceOrderingManagement/v4/serviceOrder/{so_id}",
        "state": "inProgress",
        "description": f"Provision mobile service for order {order_id}",
        "orderDate": now,
        "productOrder": {"id": order_id, "@referredType": "ProductOrder"},
        "relatedParty": record.get("relatedParty", []),
        "orderItem": [{"id": "1", "action": "add", "serviceName": "Mobile Voice + Data", "state": "inProgress"}],
        "createdAt": now, "lastUpdatedAt": now,
        "@type": "ServiceOrder", "@baseType": "ServiceOrder",
    }
    service_orders[so_id] = service_order
    _add_related_entity(record, so_id, "ServiceOrder", service_order["href"])
    product_orders[order_id] = record
    publish("ServiceOrderCreateEvent", {"serviceOrder": service_order})

    await asyncio.sleep(2)

    # Create Service in inventory (TMF638)
    record = product_orders.get(order_id)
    if not record or record.get("state") == "cancelled":
        return
    now = datetime.now(timezone.utc).isoformat()
    msisdn = _gen_msisdn()
    imsi = _gen_imsi()
    iccid = _gen_iccid()
    offering_name = "Mobile Service"
    for item in record.get("orderItem", []):
        off = item.get("productOffering", {})
        if off.get("name"):
            offering_name = off["name"]

    svc_id = str(uuid.uuid4())
    svc = {
        "id": svc_id,
        "href": f"/serviceInventory/v4/service/{svc_id}",
        "name": f"Mobile Line - {msisdn}",
        "description": f"{'eSIM' if sim_type.lower() == 'esim' else 'Physical SIM'} mobile service",
        "state": "active",
        "serviceType": "mobile",
        "category": sim_type,
        "startDate": now,
        "serviceCharacteristic": [
            {"name": "msisdn", "value": msisdn, "valueType": "string"},
            {"name": "imsi", "value": imsi, "valueType": "string"},
            {"name": "iccid", "value": iccid, "valueType": "string"},
            {"name": "simType", "value": sim_type, "valueType": "string"},
        ],
        "relatedParty": record.get("relatedParty", []),
        "productOrder": {"id": order_id, "@referredType": "ProductOrder"},
        "createdAt": now, "lastUpdatedAt": now,
        "@type": "Service", "@baseType": "Service",
    }
    services[svc_id] = svc
    _add_related_entity(record, svc_id, "Service", svc["href"])

    # Complete the service order
    service_order["state"] = "completed"
    service_order["completionDate"] = now
    service_order["lastUpdatedAt"] = now
    for si in service_order.get("orderItem", []):
        si["state"] = "completed"
    service_orders[so_id] = service_order

    _set_milestone(record, "provisioning.completed")
    product_orders[order_id] = record
    publish("ServiceCreateEvent", {"service": svc})
    publish("ServiceOrderStateChangeEvent", {"serviceOrder": {"id": so_id, "state": "completed"}})

    # =================================================================
    # STAGE 3: BILLING
    # =================================================================
    record = product_orders.get(order_id)
    if not record or record.get("state") == "cancelled":
        return

    now = datetime.now(timezone.utc).isoformat()
    _set_milestone(record, "billing.inProgress")
    product_orders[order_id] = record

    await asyncio.sleep(1)

    # Find the billing account from relatedParty or use a placeholder
    ba_ref = None
    for rp in record.get("relatedParty", []):
        customer_id = rp.get("id")
        if customer_id:
            acct_list = billing_accounts.values()
            for acct in acct_list:
                for arp in acct.get("relatedParty", []):
                    if arp.get("id") == customer_id:
                        ba_ref = {"id": acct["id"], "href": acct.get("href"), "name": acct.get("name"), "@referredType": "BillingAccount"}
                        break
                if ba_ref:
                    break
        if ba_ref:
            break

    bill_id = str(uuid.uuid4())
    bill = {
        "id": bill_id,
        "href": f"/customerBillManagement/v4/customerBill/{bill_id}",
        "state": "new",
        "runType": "onCycle",
        "description": f"First bill for order {order_id}",
        "billDate": now,
        "billingAccount": ba_ref,
        "productOrder": {"id": order_id, "@referredType": "ProductOrder"},
        "relatedParty": record.get("relatedParty", []),
        "billItem": [
            {
                "id": "1",
                "name": f"{offering_name} - Monthly charge",
                "priceType": "recurring",
                "amount": {"unit": "EUR", "value": 49.99},
            },
            {
                "id": "2",
                "name": "SIM activation fee",
                "priceType": "oneTime",
                "amount": {"unit": "EUR", "value": 9.99},
            },
        ],
        "amountDue": {"unit": "EUR", "value": 59.98},
        "taxAmount": {"unit": "EUR", "value": 11.40},
        "createdAt": now, "lastUpdatedAt": now,
        "@type": "CustomerBill", "@baseType": "CustomerBill",
    }
    customer_bills[bill_id] = bill
    _add_related_entity(record, bill_id, "CustomerBill", bill["href"])
    _set_milestone(record, "billing.completed")
    product_orders[order_id] = record
    publish("CustomerBillCreateEvent", {"customerBill": bill})

    # Update billing account balance if found
    if ba_ref:
        acct_record = billing_accounts.get(ba_ref["id"])
        if acct_record:
            for bal in acct_record.get("accountBalance", []):
                if bal.get("balanceType") == "currentBalance":
                    bal["amount"]["value"] = round(bal["amount"].get("value", 0) + 59.98, 2)
            billing_accounts[ba_ref["id"]] = acct_record

    # =================================================================
    # STAGE 4: COMPLETION
    # =================================================================
    record = product_orders.get(order_id)
    if not record or record.get("state") == "cancelled":
        return

    now = datetime.now(timezone.utc).isoformat()
    record["state"] = "completed"
    record["completionDate"] = now

    for item in record.get("orderItem", []):
        item["state"] = "completed"

    # Auto-create product inventory (TMF637)
    for item in record.get("orderItem", []):
        if item.get("action") != "add":
            continue
        offering_ref = item.get("productOffering", {})
        product_id = str(uuid.uuid4())
        inv_base = "/productInventory/v4/product"
        product_record = {
            "id": product_id,
            "href": f"{inv_base}/{product_id}",
            "name": offering_ref.get("name", "Unknown product"),
            "description": f"Provisioned from order {order_id}",
            "status": "active",
            "isBundle": False, "isCustomerVisible": True,
            "startDate": now, "terminationDate": None,
            "createdAt": now, "lastUpdatedAt": now,
            "@type": "Product", "@baseType": "Product",
            "productOffering": {
                "id": offering_ref.get("id", ""), "href": offering_ref.get("href"),
                "name": offering_ref.get("name"), "@referredType": "ProductOffering",
            },
            "relatedParty": record.get("relatedParty", []),
            "productOrderItem": [{"id": order_id, "href": record["href"], "orderItemId": item.get("id"), "@referredType": "ProductOrder"}],
        }
        product_inventory[product_id] = product_record
        _add_related_entity(record, product_id, "Product", product_record["href"])
        publish("ProductCreateEvent", {"product": product_record})

    _set_milestone(record, "completed")
    product_orders[order_id] = record
    publish("ProductOrderStateChangeEvent", {
        "productOrder": {"id": order_id, "state": "completed", "previousState": "inProgress"},
    })


# ---------------------------------------------------------------------------
# POST — place an order
# ---------------------------------------------------------------------------

@router.post(
    "/productOrder",
    response_model=ProductOrder,
    status_code=201,
    summary="Place a product order",
    response_description="Order created and fulfilment started",
)
async def create_order(
    body: ProductOrderCreate,
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    """
    Places a new ProductOrder and starts the fulfilment state machine.

    **SIM type detection:** add a `productCharacteristic` with
    `name: "simType"` and `value: "physical"` or `"eSIM"` to your
    orderItem. Physical SIM orders go through shipping; eSIM skips
    straight to provisioning.

    **Fulfilment stages (poll via GET to watch):**
    1. **Shipping** (physical SIM only): processing → shipped → delivered
    2. **Provisioning**: service order + service created with MSISDN/IMSI
    3. **Billing**: customer bill created, account balance updated
    4. **Completed**: product in inventory, order done

    Each stage updates `milestone` and appends to `milestoneHistory`.
    Related entities (Shipment, ServiceOrder, Service, CustomerBill,
    Product) appear in `relatedEntity`.

    **TMF622 spec reference:** POST /productOrder
    """
    order_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    order_data = body.model_dump(by_alias=True, exclude_none=True)

    for item in order_data.get("orderItem", []):
        item["state"] = "acknowledged"

    record = {
        "id": order_id,
        "href": f"{BASE_PATH}/{order_id}",
        "state": "acknowledged",
        "milestone": "acknowledged",
        "milestoneHistory": [{"milestone": "acknowledged", "timestamp": now}],
        "relatedEntity": [],
        "orderDate": now,
        "expectedCompletionDate": None,
        "completionDate": None,
        "lastUpdatedAt": now,
        "@type": "ProductOrder",
        "@baseType": "ProductOrder",
        **order_data,
    }

    product_orders[order_id] = record
    publish("ProductOrderCreateEvent", {"productOrder": record})
    background_tasks.add_task(_advance_order, order_id)

    return JSONResponse(content=record, status_code=201)


# ---------------------------------------------------------------------------
# GET — list orders
# ---------------------------------------------------------------------------

@router.get(
    "/productOrder",
    response_model=list[ProductOrder],
    summary="List product orders",
)
def list_orders(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    state: str | None = None,
    external_id: str | None = Query(None, alias="externalId"),
) -> JSONResponse:
    """List all orders with optional state/externalId filtering. **TMF622:** GET /productOrder"""
    results = list(product_orders.values())
    if state:
        results = [r for r in results if r.get("state") == state]
    if external_id:
        results = [r for r in results if r.get("externalId") == external_id]
    total = len(results)
    page = results[offset:offset+limit]
    return JSONResponse(content=page, headers={"X-Total-Count": str(total), "X-Result-Count": str(len(page))})


# ---------------------------------------------------------------------------
# GET — retrieve by id
# ---------------------------------------------------------------------------

@router.get(
    "/productOrder/{order_id}",
    response_model=ProductOrder,
    summary="Retrieve a product order",
)
def get_order(order_id: str) -> JSONResponse:
    """Get an order with milestone history and related entities. **TMF622:** GET /productOrder/{id}"""
    record = product_orders.get(order_id)
    if not record:
        raise HTTPException(404, detail={"code": "ERR_NOT_FOUND", "reason": f"ProductOrder {order_id} not found", "@type": "Error"})
    return JSONResponse(content=record)


# ---------------------------------------------------------------------------
# PATCH — update / cancel
# ---------------------------------------------------------------------------

@router.patch(
    "/productOrder/{order_id}",
    response_model=ProductOrder,
    summary="Update or cancel a product order",
)
def patch_order(order_id: str, body: ProductOrderUpdate) -> JSONResponse:
    """Cancel or update an order. Cancellation halts the state machine. **TMF622:** PATCH /productOrder/{id}"""
    record = product_orders.get(order_id)
    if not record:
        raise HTTPException(404, detail={"code": "ERR_NOT_FOUND", "reason": f"ProductOrder {order_id} not found", "@type": "Error"})

    updates = body.model_dump(by_alias=True, exclude_none=True)
    now = datetime.now(timezone.utc).isoformat()

    new_state = updates.get("state")
    if new_state:
        if new_state not in VALID_STATES:
            raise HTTPException(400, detail={"code": "ERR_INVALID_STATE", "reason": f"Invalid state '{new_state}'", "@type": "Error"})
        current_state = record.get("state")
        if current_state == "completed":
            raise HTTPException(409, detail={"code": "ERR_STATE_CONFLICT", "reason": "Cannot modify a completed order", "@type": "Error"})
        if new_state == "cancelled":
            record["cancellationDate"] = now
            for item in record.get("orderItem", []):
                item["state"] = "cancelled"
            _set_milestone(record, "cancelled")
            publish("ProductOrderStateChangeEvent", {
                "productOrder": {"id": order_id, "state": "cancelled", "previousState": current_state},
            })

    if "note" in updates and updates["note"]:
        existing_notes = record.get("note") or []
        for n in updates["note"]:
            n["date"] = n.get("date") or now
            n["id"] = n.get("id") or str(uuid.uuid4())[:8]
        existing_notes.extend(updates["note"])
        record["note"] = existing_notes
        del updates["note"]

    record.update(updates)
    record["lastUpdatedAt"] = now
    product_orders[order_id] = record
    return JSONResponse(content=record)


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

@router.delete("/productOrder/{order_id}", status_code=204, summary="Delete a product order")
def delete_order(order_id: str):
    """Remove an order. Stops the background state machine. **TMF622:** DELETE /productOrder/{id}"""
    record = product_orders.pop(order_id, None)
    if not record:
        raise HTTPException(404, detail={"code": "ERR_NOT_FOUND", "reason": f"ProductOrder {order_id} not found", "@type": "Error"})
    publish("ProductOrderDeleteEvent", {"productOrder": record})
    return None
