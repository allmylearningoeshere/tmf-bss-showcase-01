"""
TMF622 Product Ordering Management — Pydantic schemas.

Models follow the TMF622 v4 ProductOrder resource specification.
Fields use camelCase aliases to match the TMF JSON wire format.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# ---------------------------------------------------------------------------
# Sub-resources
# ---------------------------------------------------------------------------

class Note(BaseModel):
    """A free-text note attached to an order."""
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None
    text: str


class RelatedPartyRef(BaseModel):
    """Reference to a party (customer, sales agent, etc.)."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    href: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None
    referred_type: Optional[str] = Field(None, alias="@referredType")


class ProductOfferingRef(BaseModel):
    """Reference to the offering being ordered."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    href: Optional[str] = None
    name: Optional[str] = None
    referred_type: Optional[str] = Field(
        "ProductOffering", alias="@referredType"
    )


class ProductRef(BaseModel):
    """Reference to an existing product instance (for modify/delete actions)."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    href: Optional[str] = None
    name: Optional[str] = None
    referred_type: Optional[str] = Field(
        "Product", alias="@referredType"
    )


class OrderItemAction(BaseModel):
    """
    Describes what to do with this line item.
    TMF622 actions: add, modify, delete, noChange.
    """
    pass


class ProductOrderItem(BaseModel):
    """A single line item in a product order."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    quantity: Optional[int] = 1
    action: str = "add"
    state: Optional[str] = None
    product_offering: Optional[ProductOfferingRef] = Field(
        default=None, alias="productOffering"
    )
    product: Optional[ProductRef] = None
    at_type: Optional[str] = Field("ProductOrderItem", alias="@type")


class OrderPrice(BaseModel):
    """Price summary for the order."""
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = None
    description: Optional[str] = None
    price_type: Optional[str] = Field(None, alias="priceType")
    recurring_charge_period: Optional[str] = Field(
        None, alias="recurringChargePeriod"
    )
    price: Optional[dict] = None


# ---------------------------------------------------------------------------
# ProductOrder — create / update payloads
# ---------------------------------------------------------------------------

class ProductOrderCreate(BaseModel):
    """
    Payload for POST /productOrder.

    At minimum, provide one orderItem with a productOffering reference.
    The server generates id, href, state, and timestamps.
    """
    model_config = ConfigDict(populate_by_name=True)

    external_id: Optional[str] = Field(None, alias="externalId")
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = Field("4", alias="priority")
    requested_start_date: Optional[str] = Field(
        None, alias="requestedStartDate"
    )
    requested_completion_date: Optional[str] = Field(
        None, alias="requestedCompletionDate"
    )
    order_item: list[ProductOrderItem] = Field(
        ..., alias="orderItem", min_length=1
    )
    related_party: Optional[list[RelatedPartyRef]] = Field(
        default=None, alias="relatedParty"
    )
    note: Optional[list[Note]] = None
    order_total_price: Optional[list[OrderPrice]] = Field(
        default=None, alias="orderTotalPrice"
    )


class ProductOrderUpdate(BaseModel):
    """
    Payload for PATCH /productOrder/{id}.

    Primarily used to cancel an order or add notes.
    State changes via PATCH are limited to cancellation requests.
    """
    model_config = ConfigDict(populate_by_name=True)

    state: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    cancellation_reason: Optional[str] = Field(
        None, alias="cancellationReason"
    )
    note: Optional[list[Note]] = None


# ---------------------------------------------------------------------------
# ProductOrder — full resource (GET responses)
# ---------------------------------------------------------------------------

class ProductOrder(BaseModel):
    """
    The complete TMF622 ProductOrder resource.

    Includes server-generated fields: id, href, state, orderDate,
    completionDate, and milestone timestamps.
    """
    model_config = ConfigDict(populate_by_name=True)

    id: str
    href: str
    external_id: Optional[str] = Field(None, alias="externalId")
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = Field("4", alias="priority")
    state: str
    order_date: Optional[str] = Field(None, alias="orderDate")
    requested_start_date: Optional[str] = Field(
        None, alias="requestedStartDate"
    )
    requested_completion_date: Optional[str] = Field(
        None, alias="requestedCompletionDate"
    )
    expected_completion_date: Optional[str] = Field(
        None, alias="expectedCompletionDate"
    )
    completion_date: Optional[str] = Field(None, alias="completionDate")
    cancellation_date: Optional[str] = Field(None, alias="cancellationDate")
    cancellation_reason: Optional[str] = Field(
        None, alias="cancellationReason"
    )
    order_item: list[ProductOrderItem] = Field(..., alias="orderItem")
    related_party: Optional[list[RelatedPartyRef]] = Field(
        default=None, alias="relatedParty"
    )
    note: Optional[list[Note]] = None
    order_total_price: Optional[list[OrderPrice]] = Field(
        default=None, alias="orderTotalPrice"
    )
    at_type: str = Field("ProductOrder", alias="@type")
    at_base_type: str = Field("ProductOrder", alias="@baseType")
