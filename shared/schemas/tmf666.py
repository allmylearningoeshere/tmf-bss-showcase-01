"""
TMF666 Account Management — Pydantic schemas.

Models follow the TMF666 v4 BillingAccount resource specification.
Fields use camelCase aliases to match the TMF JSON wire format.
"""

from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# ---------------------------------------------------------------------------
# Sub-resources
# ---------------------------------------------------------------------------

class RelatedPartyRef(BaseModel):
    """Reference to a party (customer, account holder)."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    href: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None
    referred_type: Optional[str] = Field(None, alias="@referredType")


class ContactMediumRef(BaseModel):
    """Billing contact details."""
    model_config = ConfigDict(populate_by_name=True)

    medium_type: Optional[str] = Field(None, alias="mediumType")
    characteristic: Optional[dict] = None


class AccountBalance(BaseModel):
    """Current balance on the account."""
    model_config = ConfigDict(populate_by_name=True)

    balance_type: Optional[str] = Field(None, alias="balanceType")
    amount: Optional[dict] = None
    valid_for: Optional[dict] = Field(None, alias="validFor")


class PaymentMethodRef(BaseModel):
    """Reference to a payment method on file."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    href: Optional[str] = None
    name: Optional[str] = None
    referred_type: Optional[str] = Field(None, alias="@referredType")


class AccountTaxExemption(BaseModel):
    """Tax exemption information."""
    model_config = ConfigDict(populate_by_name=True)

    certificate_number: Optional[str] = Field(None, alias="certificateNumber")
    issuing_jurisdiction: Optional[str] = Field(None, alias="issuingJurisdiction")
    reason: Optional[str] = None
    valid_for: Optional[dict] = Field(None, alias="validFor")


class BillStructure(BaseModel):
    """How the bill is generated and delivered."""
    model_config = ConfigDict(populate_by_name=True)

    cycle_period: Optional[str] = Field(None, alias="cyclePeriod")
    billing_date_shift: Optional[int] = Field(None, alias="billingDateShift")
    payment_due_date_shift: Optional[int] = Field(None, alias="paymentDueDateShift")
    bill_format: Optional[str] = Field(None, alias="billFormat")
    delivery_method: Optional[str] = Field(None, alias="deliveryMethod")
    notification_contact: Optional[ContactMediumRef] = Field(
        None, alias="notificationContact"
    )


# ---------------------------------------------------------------------------
# BillingAccount — create / update payloads
# ---------------------------------------------------------------------------

class BillingAccountCreate(BaseModel):
    """
    Payload for POST /billingAccount.

    At minimum, provide a name and at least one relatedParty referencing
    the customer who owns this account.
    """
    model_config = ConfigDict(populate_by_name=True)

    name: str
    description: Optional[str] = None
    account_type: Optional[str] = Field("individual", alias="accountType")
    state: Optional[str] = None
    currency: Optional[str] = Field("EUR", alias="currency")
    credit_limit: Optional[dict] = Field(None, alias="creditLimit")
    bill_structure: Optional[BillStructure] = Field(None, alias="billStructure")
    payment_method_ref: Optional[list[PaymentMethodRef]] = Field(
        default=None, alias="paymentMethod"
    )
    tax_exemption: Optional[list[AccountTaxExemption]] = Field(
        default=None, alias="taxExemption"
    )
    related_party: Optional[list[RelatedPartyRef]] = Field(
        default=None, alias="relatedParty"
    )
    contact: Optional[list[ContactMediumRef]] = None


class BillingAccountUpdate(BaseModel):
    """
    Payload for PATCH /billingAccount/{id}.

    Every field is optional — only supplied fields are merged.
    """
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = None
    description: Optional[str] = None
    account_type: Optional[str] = Field(None, alias="accountType")
    state: Optional[str] = None
    currency: Optional[str] = None
    credit_limit: Optional[dict] = Field(None, alias="creditLimit")
    bill_structure: Optional[BillStructure] = Field(None, alias="billStructure")
    payment_method_ref: Optional[list[PaymentMethodRef]] = Field(
        default=None, alias="paymentMethod"
    )
    tax_exemption: Optional[list[AccountTaxExemption]] = Field(
        default=None, alias="taxExemption"
    )
    related_party: Optional[list[RelatedPartyRef]] = Field(
        default=None, alias="relatedParty"
    )
    contact: Optional[list[ContactMediumRef]] = None


# ---------------------------------------------------------------------------
# BillingAccount — full resource (GET responses)
# ---------------------------------------------------------------------------

class BillingAccount(BaseModel):
    """
    The complete TMF666 BillingAccount resource.

    Includes server-generated fields: id, href, state, accountBalance,
    and TMF metadata.
    """
    model_config = ConfigDict(populate_by_name=True)

    id: str
    href: str
    name: str
    description: Optional[str] = None
    account_type: Optional[str] = Field("individual", alias="accountType")
    state: str = "active"
    currency: Optional[str] = Field("EUR", alias="currency")
    credit_limit: Optional[dict] = Field(None, alias="creditLimit")
    account_balance: Optional[list[AccountBalance]] = Field(
        default=None, alias="accountBalance"
    )
    bill_structure: Optional[BillStructure] = Field(None, alias="billStructure")
    payment_method_ref: Optional[list[PaymentMethodRef]] = Field(
        default=None, alias="paymentMethod"
    )
    tax_exemption: Optional[list[AccountTaxExemption]] = Field(
        default=None, alias="taxExemption"
    )
    related_party: Optional[list[RelatedPartyRef]] = Field(
        default=None, alias="relatedParty"
    )
    contact: Optional[list[ContactMediumRef]] = None
    at_type: str = Field("BillingAccount", alias="@type")
    at_base_type: str = Field("Account", alias="@baseType")
    at_schema_location: Optional[str] = Field(None, alias="@schemaLocation")
