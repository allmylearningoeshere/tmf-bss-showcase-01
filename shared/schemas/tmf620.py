"""
TMF620 Product Catalog Management — Pydantic schemas.

Models follow the TMF620 v4 specification for ProductSpecification
and ProductOffering resources.  Fields use camelCase aliases to match
the TMF JSON wire format.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# ---------------------------------------------------------------------------
# Shared sub-resources
# ---------------------------------------------------------------------------

class TimePeriod(BaseModel):
    """A period of time, used for validity windows."""
    model_config = ConfigDict(populate_by_name=True)

    start_date_time: Optional[str] = Field(None, alias="startDateTime")
    end_date_time: Optional[str] = Field(None, alias="endDateTime")


class RelatedPartyRef(BaseModel):
    """Reference to a party playing a role relative to this resource."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    href: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None
    referred_type: Optional[str] = Field(None, alias="@referredType")


class ProductSpecCharacteristic(BaseModel):
    """A characteristic quality or attribute of a product specification."""
    model_config = ConfigDict(populate_by_name=True)

    name: str
    description: Optional[str] = None
    value_type: Optional[str] = Field(None, alias="valueType")
    configurable: Optional[bool] = False
    product_spec_characteristic_value: Optional[list[dict]] = Field(
        default=None, alias="productSpecCharacteristicValue"
    )


# ---------------------------------------------------------------------------
# ProductOfferingPrice
# ---------------------------------------------------------------------------

class ProductOfferingPriceCreate(BaseModel):
    """Payload for creating a price component on an offering."""
    model_config = ConfigDict(populate_by_name=True)

    name: str
    description: Optional[str] = None
    price_type: Optional[str] = Field(None, alias="priceType")
    recurring_charge_period_type: Optional[str] = Field(
        None, alias="recurringChargePeriodType"
    )
    recurring_charge_period_length: Optional[int] = Field(
        None, alias="recurringChargePeriodLength"
    )
    is_bundle: Optional[bool] = Field(False, alias="isBundle")
    lifecycle_status: Optional[str] = Field(None, alias="lifecycleStatus")
    price: Optional[dict] = None
    unit_of_measure: Optional[str] = Field(None, alias="unitOfMeasure")
    valid_for: Optional[TimePeriod] = Field(None, alias="validFor")


class ProductOfferingPrice(ProductOfferingPriceCreate):
    """Full price resource with server-generated fields."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    href: str
    at_type: str = Field("ProductOfferingPrice", alias="@type")


# ---------------------------------------------------------------------------
# ProductSpecification
# ---------------------------------------------------------------------------

class ProductSpecificationCreate(BaseModel):
    """Payload for POST /productSpecification."""
    model_config = ConfigDict(populate_by_name=True)

    name: str
    description: Optional[str] = None
    brand: Optional[str] = None
    product_number: Optional[str] = Field(None, alias="productNumber")
    is_bundle: Optional[bool] = Field(False, alias="isBundle")
    lifecycle_status: Optional[str] = Field("Active", alias="lifecycleStatus")
    valid_for: Optional[TimePeriod] = Field(None, alias="validFor")
    product_spec_characteristic: Optional[list[ProductSpecCharacteristic]] = Field(
        default=None, alias="productSpecCharacteristic"
    )
    related_party: Optional[list[RelatedPartyRef]] = Field(
        default=None, alias="relatedParty"
    )


class ProductSpecificationUpdate(BaseModel):
    """Payload for PATCH /productSpecification/{id}."""
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    product_number: Optional[str] = Field(None, alias="productNumber")
    is_bundle: Optional[bool] = Field(None, alias="isBundle")
    lifecycle_status: Optional[str] = Field(None, alias="lifecycleStatus")
    valid_for: Optional[TimePeriod] = Field(None, alias="validFor")
    product_spec_characteristic: Optional[list[ProductSpecCharacteristic]] = Field(
        default=None, alias="productSpecCharacteristic"
    )
    related_party: Optional[list[RelatedPartyRef]] = Field(
        default=None, alias="relatedParty"
    )


class ProductSpecification(ProductSpecificationCreate):
    """Full product specification resource with server-generated fields."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    href: str
    at_type: str = Field("ProductSpecification", alias="@type")
    at_base_type: str = Field("ProductSpecification", alias="@baseType")
    last_update: Optional[str] = Field(None, alias="lastUpdate")


# ---------------------------------------------------------------------------
# ProductOffering
# ---------------------------------------------------------------------------

class ProductSpecificationRef(BaseModel):
    """A reference to a ProductSpecification."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    href: Optional[str] = None
    name: Optional[str] = None
    version: Optional[str] = None
    referred_type: Optional[str] = Field(
        "ProductSpecification", alias="@referredType"
    )


class ProductOfferingPriceRef(BaseModel):
    """A reference to a ProductOfferingPrice."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    href: Optional[str] = None
    name: Optional[str] = None
    referred_type: Optional[str] = Field(
        "ProductOfferingPrice", alias="@referredType"
    )


class ProductOfferingCreate(BaseModel):
    """Payload for POST /productOffering."""
    model_config = ConfigDict(populate_by_name=True)

    name: str
    description: Optional[str] = None
    is_bundle: Optional[bool] = Field(False, alias="isBundle")
    is_sellable: Optional[bool] = Field(True, alias="isSellable")
    lifecycle_status: Optional[str] = Field("Active", alias="lifecycleStatus")
    status_reason: Optional[str] = Field(None, alias="statusReason")
    version: Optional[str] = None
    valid_for: Optional[TimePeriod] = Field(None, alias="validFor")
    product_specification: Optional[ProductSpecificationRef] = Field(
        default=None, alias="productSpecification"
    )
    product_offering_price: Optional[list[ProductOfferingPriceRef]] = Field(
        default=None, alias="productOfferingPrice"
    )
    related_party: Optional[list[RelatedPartyRef]] = Field(
        default=None, alias="relatedParty"
    )


class ProductOfferingUpdate(BaseModel):
    """Payload for PATCH /productOffering/{id}."""
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = None
    description: Optional[str] = None
    is_bundle: Optional[bool] = Field(None, alias="isBundle")
    is_sellable: Optional[bool] = Field(None, alias="isSellable")
    lifecycle_status: Optional[str] = Field(None, alias="lifecycleStatus")
    status_reason: Optional[str] = Field(None, alias="statusReason")
    version: Optional[str] = None
    valid_for: Optional[TimePeriod] = Field(None, alias="validFor")
    product_specification: Optional[ProductSpecificationRef] = Field(
        default=None, alias="productSpecification"
    )
    product_offering_price: Optional[list[ProductOfferingPriceRef]] = Field(
        default=None, alias="productOfferingPrice"
    )
    related_party: Optional[list[RelatedPartyRef]] = Field(
        default=None, alias="relatedParty"
    )


class ProductOffering(ProductOfferingCreate):
    """Full product offering resource with server-generated fields."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    href: str
    at_type: str = Field("ProductOffering", alias="@type")
    at_base_type: str = Field("ProductOffering", alias="@baseType")
    last_update: Optional[str] = Field(None, alias="lastUpdate")
