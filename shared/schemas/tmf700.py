"""TMF700 Shipment Tracking — Pydantic schemas."""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ShippingAddress(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    street1: Optional[str] = None
    street2: Optional[str] = None
    city: Optional[str] = None
    state_or_province: Optional[str] = Field(None, alias="stateOrProvince")
    post_code: Optional[str] = Field(None, alias="postCode")
    country: Optional[str] = None


class ProductOrderRef(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    href: Optional[str] = None
    referred_type: Optional[str] = Field("ProductOrder", alias="@referredType")


class ShipmentItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    quantity: Optional[int] = 1
    description: Optional[str] = None


class ShipmentCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    description: Optional[str] = None
    carrier: Optional[str] = None
    tracking_number: Optional[str] = Field(None, alias="trackingNumber")
    shipping_address: Optional[ShippingAddress] = Field(None, alias="shippingAddress")
    product_order: Optional[ProductOrderRef] = Field(None, alias="productOrder")
    shipment_item: Optional[list[ShipmentItem]] = Field(None, alias="shipmentItem")


class ShipmentUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    status: Optional[str] = None
    carrier: Optional[str] = None
    tracking_number: Optional[str] = Field(None, alias="trackingNumber")
    description: Optional[str] = None


class Shipment(ShipmentCreate):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    href: str
    status: str = "processing"
    status_history: Optional[list[dict]] = Field(None, alias="statusHistory")
    at_type: str = Field("Shipment", alias="@type")
    at_base_type: str = Field("Shipment", alias="@baseType")
