"""
Shared in-memory store.

A single module-level dict per domain.  All services import from here so
that data created in one router is immediately visible in another — no
inter-process networking required.  Data is intentionally ephemeral:
every restart gives a clean slate, which is fine for a showcase.
"""

from typing import Any

# keyed by UUID string
individuals: dict[str, Any] = {}
organisations: dict[str, Any] = {}
product_specifications: dict[str, Any] = {}
product_offerings: dict[str, Any] = {}
product_orders: dict[str, Any] = {}
