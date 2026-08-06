"""TMF638 Service Inventory — Pydantic schemas."""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ServiceCharacteristic(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    name: str
    value: str
    value_type: Optional[str] = Field(None, alias="valueType")


class ServiceSpecificationRef(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    href: Optional[str] = None
    name: Optional[str] = None
    referred_type: Optional[str] = Field("ServiceSpecification", alias="@referredType")


class RelatedPartyRef(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    href: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None
    referred_type: Optional[str] = Field(None, alias="@referredType")


class ProductOrderRef(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    href: Optional[str] = None
    referred_type: Optional[str] = Field("ProductOrder", alias="@referredType")


class ServiceCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    service_type: Optional[str] = Field(None, alias="serviceType")
    service_specification: Optional[ServiceSpecificationRef] = Field(None, alias="serviceSpecification")
    service_characteristic: Optional[list[ServiceCharacteristic]] = Field(None, alias="serviceCharacteristic")
    related_party: Optional[list[RelatedPartyRef]] = Field(None, alias="relatedParty")
    product_order: Optional[ProductOrderRef] = Field(None, alias="productOrder")


class ServiceUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    state: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    service_characteristic: Optional[list[ServiceCharacteristic]] = Field(None, alias="serviceCharacteristic")


class Service(ServiceCreate):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    href: str
    state: str = "active"
    start_date: Optional[str] = Field(None, alias="startDate")
    end_date: Optional[str] = Field(None, alias="endDate")
    at_type: str = Field("Service", alias="@type")
    at_base_type: str = Field("Service", alias="@baseType")
