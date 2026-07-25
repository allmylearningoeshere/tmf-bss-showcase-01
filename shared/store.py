"""
Entity stores.

Historically these were plain in-memory dicts, which meant every record was
lost whenever the process restarted. They are now database-backed `Store`
objects that expose the same dict-shaped interface (`store[id] = record`,
`.get()`, `.values()`, `.pop()`), so the service routers continue to work
unchanged while their data persists in Postgres.

See `shared/db/repository.py` for the implementation and `shared/db/models.py`
for the schema.
"""

from shared.db.repository import (  # noqa: F401
    billing_accounts,
    customers,
    individuals,
    organisations,
    product_inventory,
    product_offerings,
    product_orders,
    product_specifications,
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
]
