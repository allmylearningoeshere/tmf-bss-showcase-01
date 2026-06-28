"""
TMF637 Product Inventory — Pydantic schemas.

A Product in inventory represents what a customer actually has — an
active subscription, an installed service, a provisioned line.  Products
are created automatically when orders complete and can be suspended,
modified, or terminated.
"""

from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# ---------------------------------------------------------------------------
# Sub-resources
# ---------------------------------------------------------------------------

class ProductOfferingRef(BaseModel):
    """Reference to the offering this product was ordered from."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    href: Optional[str] = None
    name: Optional[str] = None
    referred_type: Optional[str] = Field(
        "ProductOffering", alias="@referredType"
    )


class ProductSpecificationRef(BaseModel):
    """Reference to the specification this product implements."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    href: Optional[str] = None
    name: Optional[str] = None
    referred_type: Optional[str] = Field(
        "ProductSpecification", alias="@referredType"
    )


class RelatedPartyRef(BaseModel):
    """Reference to the customer who owns this product."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    href: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None
    referred_type: Optional[str] = Field(None, alias="@referredType")


class BillingAccountRef(BaseModel):
    """Reference to the billing account charged for this product."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    href: Optional[str] = None
    name: Optional[str] = None
    referred_type: Optional[str] = Field(
        "BillingAccount", alias="@referredType"
    )


class ProductOrderRef(BaseModel):
    """Reference to the order that created this product."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    href: Optional[str] = None
    order_item_id: Optional[str] = Field(None, alias="orderItemId")
    referred_type: Optional[str] = Field(
        "ProductOrder", alias="@referredType"
    )


class ProductCharacteristic(BaseModel):
    """A runtime characteristic of the product instance."""
    model_config = ConfigDict(populate_by_name=True)

    name: str
    value_type: Optional[str] = Field(None, alias="valueType")
    value: str


class ProductPrice(BaseModel):
    """Recurring or one-time price applied to this product."""
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = None
    description: Optional[str] = None
    price_type: Optional[str] = Field(None, alias="priceType")
    recurring_charge_period: Optional[str] = Field(
        None, alias="recurringChargePeriod"
    )
    price: Optional[dict] = None


# ---------------------------------------------------------------------------
# Product — create / update payloads
# ---------------------------------------------------------------------------

class ProductCreate(BaseModel):
    """
    Payload for POST /product.

    Typically auto-created by the order fulfilment process, but can
    also be created manually for migrations or bulk imports.
    """
    model_config = ConfigDict(populate_by_name=True)

    name: str
    description: Optional[str] = None
    status: Optional[str] = None
    is_bundle: Optional[bool] = Field(False, alias="isBundle")
    is_customer_visible: Optional[bool] = Field(True, alias="isCustomerVisible")
    product_offering: Optional[ProductOfferingRef] = Field(
        default=None, alias="productOffering"
    )
    product_specification: Optional[ProductSpecificationRef] = Field(
        default=None, alias="productSpecification"
    )
    related_party: Optional[list[RelatedPartyRef]] = Field(
        default=None, alias="relatedParty"
    )
    billing_account: Optional[BillingAccountRef] = Field(
        default=None, alias="billingAccount"
    )
    product_order_item: Optional[list[ProductOrderRef]] = Field(
        default=None, alias="productOrderItem"
    )
    product_characteristic: Optional[list[ProductCharacteristic]] = Field(
        default=None, alias="productCharacteristic"
    )
    product_price: Optional[list[ProductPrice]] = Field(
        default=None, alias="productPrice"
    )


class ProductUpdate(BaseModel):
    """
    Payload for PATCH /product/{id}.

    Common operations: change status (active → suspended → terminated),
    update characteristics, modify pricing.
    """
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    is_customer_visible: Optional[bool] = Field(None, alias="isCustomerVisible")
    related_party: Optional[list[RelatedPartyRef]] = Field(
        default=None, alias="relatedParty"
    )
    billing_account: Optional[BillingAccountRef] = Field(
        default=None, alias="billingAccount"
    )
    product_characteristic: Optional[list[ProductCharacteristic]] = Field(
        default=None, alias="productCharacteristic"
    )
    product_price: Optional[list[ProductPrice]] = Field(
        default=None, alias="productPrice"
    )


# ---------------------------------------------------------------------------
# Product — full resource (GET responses)
# ---------------------------------------------------------------------------

class Product(BaseModel):
    """
    The complete TMF637 Product resource.

    Represents an active product instance in a customer's inventory —
    what they actually have, as opposed to what the catalog offers.
    """
    model_config = ConfigDict(populate_by_name=True)

    id: str
    href: str
    name: str
    description: Optional[str] = None
    status: str = "active"
    is_bundle: Optional[bool] = Field(False, alias="isBundle")
    is_customer_visible: Optional[bool] = Field(True, alias="isCustomerVisible")
    start_date: Optional[str] = Field(None, alias="startDate")
    termination_date: Optional[str] = Field(None, alias="terminationDate")
    product_offering: Optional[ProductOfferingRef] = Field(
        default=None, alias="productOffering"
    )
    product_specification: Optional[ProductSpecificationRef] = Field(
        default=None, alias="productSpecification"
    )
    related_party: Optional[list[RelatedPartyRef]] = Field(
        default=None, alias="relatedParty"
    )
    billing_account: Optional[BillingAccountRef] = Field(
        default=None, alias="billingAccount"
    )
    product_order_item: Optional[list[ProductOrderRef]] = Field(
        default=None, alias="productOrderItem"
    )
    product_characteristic: Optional[list[ProductCharacteristic]] = Field(
        default=None, alias="productCharacteristic"
    )
    product_price: Optional[list[ProductPrice]] = Field(
        default=None, alias="productPrice"
    )
    at_type: str = Field("Product", alias="@type")
    at_base_type: str = Field("Product", alias="@baseType")
