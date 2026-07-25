"""
TMF629 Customer Management — Pydantic schemas.

A Customer is a Party that has entered into a commercial relationship.
The Customer resource wraps a party reference and adds customer-specific
attributes like status, category, and linked accounts.
"""

from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# ---------------------------------------------------------------------------
# Sub-resources
# ---------------------------------------------------------------------------

class RelatedPartyRef(BaseModel):
    """Reference to the underlying party (Individual or Organisation)."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    href: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None
    referred_type: Optional[str] = Field(None, alias="@referredType")


class AccountRef(BaseModel):
    """Reference to a linked billing or financial account."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    href: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    referred_type: Optional[str] = Field(
        "BillingAccount", alias="@referredType"
    )


class ContactMediumRef(BaseModel):
    """Preferred contact method for this customer relationship."""
    model_config = ConfigDict(populate_by_name=True)

    medium_type: Optional[str] = Field(None, alias="mediumType")
    preferred: Optional[bool] = False
    characteristic: Optional[dict] = None


class CustomerCharacteristic(BaseModel):
    """A key-value attribute of the customer relationship."""
    model_config = ConfigDict(populate_by_name=True)

    name: str
    value_type: Optional[str] = Field(None, alias="valueType")
    value: str


class CustomerCreditProfile(BaseModel):
    """Credit assessment for the customer."""
    model_config = ConfigDict(populate_by_name=True)

    credit_profile_date: Optional[str] = Field(None, alias="creditProfileDate")
    credit_risk_rating: Optional[int] = Field(None, alias="creditRiskRating")
    credit_score: Optional[int] = Field(None, alias="creditScore")
    valid_for: Optional[dict] = Field(None, alias="validFor")


# ---------------------------------------------------------------------------
# Customer — create / update payloads
# ---------------------------------------------------------------------------

class CustomerCreate(BaseModel):
    """
    Payload for POST /customer.

    At minimum, provide a name and an engaged_party referencing the
    underlying Individual or Organisation from TMF632.
    """
    model_config = ConfigDict(populate_by_name=True)

    name: str
    description: Optional[str] = None
    status: Optional[str] = None
    status_reason: Optional[str] = Field(None, alias="statusReason")
    customer_category: Optional[str] = Field(None, alias="customerCategory")
    customer_rank: Optional[str] = Field(None, alias="customerRank")
    engaged_party: RelatedPartyRef = Field(..., alias="engagedParty")
    account: Optional[list[AccountRef]] = None
    contact_medium: Optional[list[ContactMediumRef]] = Field(
        default=None, alias="contactMedium"
    )
    characteristic: Optional[list[CustomerCharacteristic]] = None
    credit_profile: Optional[list[CustomerCreditProfile]] = Field(
        default=None, alias="creditProfile"
    )
    valid_for: Optional[dict] = Field(None, alias="validFor")


class CustomerUpdate(BaseModel):
    """
    Payload for PATCH /customer/{id}.

    Every field is optional — only supplied fields are merged.
    """
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    status_reason: Optional[str] = Field(None, alias="statusReason")
    customer_category: Optional[str] = Field(None, alias="customerCategory")
    customer_rank: Optional[str] = Field(None, alias="customerRank")
    engaged_party: Optional[RelatedPartyRef] = Field(None, alias="engagedParty")
    account: Optional[list[AccountRef]] = None
    contact_medium: Optional[list[ContactMediumRef]] = Field(
        default=None, alias="contactMedium"
    )
    characteristic: Optional[list[CustomerCharacteristic]] = None
    credit_profile: Optional[list[CustomerCreditProfile]] = Field(
        default=None, alias="creditProfile"
    )
    valid_for: Optional[dict] = Field(None, alias="validFor")


# ---------------------------------------------------------------------------
# Customer — full resource (GET responses)
# ---------------------------------------------------------------------------

class Customer(BaseModel):
    """
    The complete TMF629 Customer resource.

    A Customer wraps a Party (Individual or Organisation) and represents
    the commercial relationship.
    """
    model_config = ConfigDict(populate_by_name=True)

    id: str
    href: str
    name: str
    description: Optional[str] = None
    status: str = "approved"
    status_reason: Optional[str] = Field(None, alias="statusReason")
    customer_category: Optional[str] = Field(None, alias="customerCategory")
    customer_rank: Optional[str] = Field(None, alias="customerRank")
    engaged_party: RelatedPartyRef = Field(..., alias="engagedParty")
    account: Optional[list[AccountRef]] = None
    contact_medium: Optional[list[ContactMediumRef]] = Field(
        default=None, alias="contactMedium"
    )
    characteristic: Optional[list[CustomerCharacteristic]] = None
    credit_profile: Optional[list[CustomerCreditProfile]] = Field(
        default=None, alias="creditProfile"
    )
    valid_for: Optional[dict] = Field(None, alias="validFor")
    at_type: str = Field("Customer", alias="@type")
    at_base_type: str = Field("Customer", alias="@baseType")
