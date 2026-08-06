"""TMF641 Service Order Management — Pydantic schemas."""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ServiceOrderItemRef(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    action: str = "add"
    service_name: Optional[str] = Field(None, alias="serviceName")
    state: Optional[str] = None


class ProductOrderRef(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    href: Optional[str] = None
    referred_type: Optional[str] = Field("ProductOrder", alias="@referredType")


class RelatedPartyRef(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    href: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None
    referred_type: Optional[str] = Field(None, alias="@referredType")


class ServiceOrderCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = Field("4", alias="priority")
    product_order: Optional[ProductOrderRef] = Field(None, alias="productOrder")
    related_party: Optional[list[RelatedPartyRef]] = Field(None, alias="relatedParty")
    order_item: Optional[list[ServiceOrderItemRef]] = Field(None, alias="orderItem")


class ServiceOrderUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    state: Optional[str] = None
    description: Optional[str] = None


class ServiceOrder(ServiceOrderCreate):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    href: str
    state: str = "acknowledged"
    order_date: Optional[str] = Field(None, alias="orderDate")
    completion_date: Optional[str] = Field(None, alias="completionDate")
    at_type: str = Field("ServiceOrder", alias="@type")
    at_base_type: str = Field("ServiceOrder", alias="@baseType")
