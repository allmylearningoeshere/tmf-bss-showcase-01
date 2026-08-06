"""
SQLAlchemy models for the TMF entities.

Schema strategy — hybrid:
  * Typed columns for anything we filter, sort, or join on (ids, names,
    states, timestamps, and the foreign keys that correlate entities).
  * A `doc` JSON column holding the complete TMF resource exactly as the API
    returns it. Reads serve `doc` straight back, so the API contract is
    unchanged and nested TMF structures never need shredding into columns.

The foreign keys are what make the lifecycle traceable end to end:

    Individual ──< Customer ──< BillingAccount
                       │
                       └──< ProductOrder ──< Product (inventory)

Every relationship is nullable. TMF resources can legitimately be created
standalone (an individual with no customer yet, an order placed without a
resolvable customer record), and a showcase should degrade gracefully rather
than reject a valid TMF payload on a referential technicality.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON

from shared.db.session import Base, IS_SQLITE

# JSONB on Postgres (indexable, binary); plain JSON on SQLite for local dev.
JSONDoc = JSON().with_variant(JSONB(), "postgresql") if IS_SQLITE else JSONB()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    """Server-side creation / update timestamps, separate from the TMF doc."""

    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )


# ---------------------------------------------------------------------------
# TMF632 — Party
# ---------------------------------------------------------------------------

class Individual(Base, TimestampMixin):
    __tablename__ = "individuals"

    id = Column(String(64), primary_key=True)
    full_name = Column(String(255), index=True)
    email = Column(String(255), index=True)
    status = Column(String(64), index=True)
    doc = Column(JSONDoc, nullable=False)


class Organisation(Base, TimestampMixin):
    __tablename__ = "organisations"

    id = Column(String(64), primary_key=True)
    name = Column(String(255), index=True)
    status = Column(String(64), index=True)
    doc = Column(JSONDoc, nullable=False)


# ---------------------------------------------------------------------------
# TMF629 — Customer
# ---------------------------------------------------------------------------

class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    id = Column(String(64), primary_key=True)
    name = Column(String(255), index=True)
    status = Column(String(64), index=True)
    # Correlation: the party this customer represents.
    party_id = Column(
        String(64), ForeignKey("individuals.id", ondelete="SET NULL"), index=True
    )
    doc = Column(JSONDoc, nullable=False)


# ---------------------------------------------------------------------------
# TMF666 — Billing Account
# ---------------------------------------------------------------------------

class BillingAccount(Base, TimestampMixin):
    __tablename__ = "billing_accounts"

    id = Column(String(64), primary_key=True)
    name = Column(String(255), index=True)
    state = Column(String(64), index=True)
    # Correlation: the customer who owns this account.
    customer_id = Column(
        String(64), ForeignKey("customers.id", ondelete="SET NULL"), index=True
    )
    doc = Column(JSONDoc, nullable=False)


# ---------------------------------------------------------------------------
# TMF620 — Product Catalog
# ---------------------------------------------------------------------------

class ProductSpecification(Base, TimestampMixin):
    __tablename__ = "product_specifications"

    id = Column(String(64), primary_key=True)
    name = Column(String(255), index=True)
    doc = Column(JSONDoc, nullable=False)


class ProductOffering(Base, TimestampMixin):
    __tablename__ = "product_offerings"

    id = Column(String(64), primary_key=True)
    name = Column(String(255), index=True)
    lifecycle_status = Column(String(64), index=True)
    doc = Column(JSONDoc, nullable=False)


# ---------------------------------------------------------------------------
# TMF622 — Product Order
# ---------------------------------------------------------------------------

class ProductOrder(Base, TimestampMixin):
    __tablename__ = "product_orders"

    id = Column(String(64), primary_key=True)
    state = Column(String(64), index=True)
    # Correlation: who placed the order, and for which offering.
    customer_id = Column(
        String(64), ForeignKey("customers.id", ondelete="SET NULL"), index=True
    )
    offering_id = Column(String(64), index=True)
    doc = Column(JSONDoc, nullable=False)


# ---------------------------------------------------------------------------
# TMF637 — Product Inventory
# ---------------------------------------------------------------------------

class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id = Column(String(64), primary_key=True)
    name = Column(String(255), index=True)
    status = Column(String(64), index=True)
    # Correlation: the order that provisioned this product, and its customer.
    order_id = Column(
        String(64), ForeignKey("product_orders.id", ondelete="SET NULL"), index=True
    )
    customer_id = Column(
        String(64), ForeignKey("customers.id", ondelete="SET NULL"), index=True
    )
    offering_id = Column(String(64), index=True)
    doc = Column(JSONDoc, nullable=False)


# ---------------------------------------------------------------------------
# TMF688 — Event log (optional but useful for the event feed)
# ---------------------------------------------------------------------------

class EventRecord(Base, TimestampMixin):
    __tablename__ = "events"

    id = Column(String(64), primary_key=True)
    event_type = Column(String(128), index=True)
    payload = Column(JSONDoc, nullable=False)


# Composite index: the retrieve screens look products up by order.
Index("ix_products_order_customer", Product.order_id, Product.customer_id)


# ---------------------------------------------------------------------------
# TMF700 — Shipment Tracking
# ---------------------------------------------------------------------------

class Shipment(Base, TimestampMixin):
    __tablename__ = "shipments"

    id = Column(String(64), primary_key=True)
    status = Column(String(64), index=True)
    order_id = Column(
        String(64), ForeignKey("product_orders.id", ondelete="SET NULL"), index=True
    )
    tracking_number = Column(String(128), index=True)
    doc = Column(JSONDoc, nullable=False)


# ---------------------------------------------------------------------------
# TMF641 — Service Order
# ---------------------------------------------------------------------------

class ServiceOrder(Base, TimestampMixin):
    __tablename__ = "service_orders"

    id = Column(String(64), primary_key=True)
    state = Column(String(64), index=True)
    order_id = Column(
        String(64), ForeignKey("product_orders.id", ondelete="SET NULL"), index=True
    )
    doc = Column(JSONDoc, nullable=False)


# ---------------------------------------------------------------------------
# TMF638 — Service Inventory
# ---------------------------------------------------------------------------

class Service(Base, TimestampMixin):
    __tablename__ = "services"

    id = Column(String(64), primary_key=True)
    name = Column(String(255), index=True)
    state = Column(String(64), index=True)
    order_id = Column(
        String(64), ForeignKey("product_orders.id", ondelete="SET NULL"), index=True
    )
    customer_id = Column(
        String(64), ForeignKey("customers.id", ondelete="SET NULL"), index=True
    )
    doc = Column(JSONDoc, nullable=False)


# ---------------------------------------------------------------------------
# TMF678 — Customer Bill
# ---------------------------------------------------------------------------

class CustomerBill(Base, TimestampMixin):
    __tablename__ = "customer_bills"

    id = Column(String(64), primary_key=True)
    state = Column(String(64), index=True)
    billing_account_id = Column(
        String(64), ForeignKey("billing_accounts.id", ondelete="SET NULL"), index=True
    )
    order_id = Column(
        String(64), ForeignKey("product_orders.id", ondelete="SET NULL"), index=True
    )
    doc = Column(JSONDoc, nullable=False)
