"""
Entity stores — database-backed Store objects with dict-shaped interface.
See `shared/db/repository.py` for the implementation.
"""

from shared.db.repository import (  # noqa: F401
    billing_accounts,
    customer_bills,
    customers,
    individuals,
    organisations,
    product_inventory,
    product_offerings,
    product_orders,
    product_specifications,
    service_orders,
    services,
    shipments,
)

__all__ = [
    "individuals",
    "organisations",
    "customers",
    "billing_accounts",
    "product_specifications",
    "product_offerings",
    "product_orders",
    "product_inventory",
    "shipments",
    "service_orders",
    "services",
    "customer_bills",
]
