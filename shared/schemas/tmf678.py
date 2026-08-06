"""TMF678 Customer Bill Management — Pydantic schemas."""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class BillingAccountRef(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    href: Optional[str] = None
    name: Optional[str] = None
    referred_type: Optional[str] = Field("BillingAccount", alias="@referredType")


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


class AppliedPayment(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    applied_amount: Optional[dict] = Field(None, alias="appliedAmount")
    payment_date: Optional[str] = Field(None, alias="paymentDate")


class BillItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    period_start: Optional[str] = Field(None, alias="periodStart")
    period_end: Optional[str] = Field(None, alias="periodEnd")
    price_type: Optional[str] = Field(None, alias="priceType")
    amount: Optional[dict] = None


class CustomerBillCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    description: Optional[str] = None
    bill_date: Optional[str] = Field(None, alias="billDate")
    billing_period_start: Optional[str] = Field(None, alias="billingPeriodStart")
    billing_period_end: Optional[str] = Field(None, alias="billingPeriodEnd")
    billing_account: Optional[BillingAccountRef] = Field(None, alias="billingAccount")
    product_order: Optional[ProductOrderRef] = Field(None, alias="productOrder")
    related_party: Optional[list[RelatedPartyRef]] = Field(None, alias="relatedParty")
    bill_item: Optional[list[BillItem]] = Field(None, alias="billItem")
    amount_due: Optional[dict] = Field(None, alias="amountDue")
    tax_amount: Optional[dict] = Field(None, alias="taxAmount")


class CustomerBillUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    state: Optional[str] = None
    description: Optional[str] = None
    applied_payment: Optional[list[AppliedPayment]] = Field(None, alias="appliedPayment")


class CustomerBill(CustomerBillCreate):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    href: str
    state: str = "new"
    run_type: Optional[str] = Field("onCycle", alias="runType")
    at_type: str = Field("CustomerBill", alias="@type")
    at_base_type: str = Field("CustomerBill", alias="@baseType")
