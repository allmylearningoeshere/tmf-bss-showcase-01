"""
Repository layer — a thin, dict-shaped façade over the database.

The service routers were written against plain dicts (`individuals[id] = rec`,
`individuals.get(id)`, `individuals.values()`). Rather than rewrite every
router's control flow, each store is replaced by a `Store` object exposing the
same handful of operations, backed by SQLAlchemy.

That keeps the migration mechanical and low-risk: the call sites barely change,
the TMF payloads are untouched, and the API contract stays identical.

Each store also extracts a few queryable columns from the TMF document on
write (`_columns`), which is what powers the correlation and the retrieve
screens. The full document is always stored verbatim in `doc` and returned
verbatim on read.
"""

from typing import Any, Callable, Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from shared.db import models
from shared.db.session import SessionLocal, ensure_initialised


class Store:
    """
    Dict-like persistence for one TMF entity type.

    Supported operations mirror the dict API the routers already use:
        store[id] = record        upsert
        store.get(id)             fetch one, or None
        store.values()            all records
        store.pop(id, None)       delete and return
        id in store               existence check
        len(store)                count
    """

    def __init__(
        self,
        model: type,
        columns: Callable[[dict], dict] | None = None,
    ) -> None:
        self._model = model
        self._columns = columns or (lambda doc: {})

    # -- internal ----------------------------------------------------------

    def _session(self) -> Session:
        ensure_initialised()
        return SessionLocal()

    # -- write -------------------------------------------------------------

    def __setitem__(self, key: str, record: dict) -> None:
        """Insert or update the record, refreshing the queryable columns."""
        with self._session() as db:
            row = db.get(self._model, key)
            values = self._columns(record)
            if row is None:
                row = self._model(id=key, doc=record, **values)
                db.add(row)
            else:
                row.doc = record
                for field, value in values.items():
                    setattr(row, field, value)
            db.commit()

    def save(self, record: dict) -> dict:
        """Convenience: persist a record keyed by its own `id`."""
        self[record["id"]] = record
        return record

    # -- read --------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        with self._session() as db:
            row = db.get(self._model, key)
            return row.doc if row else default

    def __getitem__(self, key: str) -> dict:
        row = self.get(key)
        if row is None:
            raise KeyError(key)
        return row

    def __contains__(self, key: str) -> bool:
        with self._session() as db:
            return db.get(self._model, key) is not None

    def values(self) -> list[dict]:
        """All records, newest first."""
        with self._session() as db:
            rows = db.execute(
                select(self._model).order_by(self._model.created_at.desc())
            ).scalars().all()
            return [r.doc for r in rows]

    def items(self) -> list[tuple[str, dict]]:
        with self._session() as db:
            rows = db.execute(
                select(self._model).order_by(self._model.created_at.desc())
            ).scalars().all()
            return [(r.id, r.doc) for r in rows]

    def keys(self) -> list[str]:
        with self._session() as db:
            rows = db.execute(select(self._model.id)).scalars().all()
            return list(rows)

    def __iter__(self) -> Iterable[str]:
        return iter(self.keys())

    def __len__(self) -> int:
        with self._session() as db:
            return db.query(self._model).count()

    # -- delete ------------------------------------------------------------

    def pop(self, key: str, default: Any = None) -> Any:
        with self._session() as db:
            row = db.get(self._model, key)
            if row is None:
                return default
            doc = row.doc
            db.delete(row)
            db.commit()
            return doc

    # -- query helpers used by the retrieve screens ------------------------

    def find_by(self, **filters) -> list[dict]:
        """Filter on the typed columns, e.g. `find_by(order_id="...")`."""
        with self._session() as db:
            stmt = select(self._model)
            for field, value in filters.items():
                stmt = stmt.where(getattr(self._model, field) == value)
            stmt = stmt.order_by(self._model.created_at.desc())
            rows = db.execute(stmt).scalars().all()
            return [r.doc for r in rows]


# ---------------------------------------------------------------------------
# Column extractors — pull queryable fields out of each TMF document.
# ---------------------------------------------------------------------------

def _first_email(doc: dict) -> str | None:
    for medium in doc.get("contactMedium") or []:
        characteristic = medium.get("characteristic") or {}
        email = characteristic.get("emailAddress")
        if email:
            return email
    return None


def _individual_columns(doc: dict) -> dict:
    return {
        "full_name": doc.get("fullName"),
        "email": _first_email(doc),
        "status": doc.get("status"),
    }


def _organisation_columns(doc: dict) -> dict:
    return {"name": doc.get("name"), "status": doc.get("status")}


def _customer_columns(doc: dict) -> dict:
    engaged = doc.get("engagedParty") or {}
    return {
        "name": doc.get("name"),
        "status": doc.get("status"),
        "party_id": engaged.get("id"),
    }


def _related_party_id(doc: dict, role: str = "customer") -> str | None:
    """Find the id of a related party with the given role."""
    for party in doc.get("relatedParty") or []:
        if (party.get("role") or "").lower() == role:
            return party.get("id")
    # Fall back to the first related party if no role matched.
    parties = doc.get("relatedParty") or []
    return parties[0].get("id") if parties else None


def _billing_account_columns(doc: dict) -> dict:
    return {
        "name": doc.get("name"),
        "state": doc.get("state"),
        "customer_id": _related_party_id(doc),
    }


def _offering_columns(doc: dict) -> dict:
    return {
        "name": doc.get("name"),
        "lifecycle_status": doc.get("lifecycleStatus"),
    }


def _spec_columns(doc: dict) -> dict:
    return {"name": doc.get("name")}


def _first_offering_id(doc: dict) -> str | None:
    for item in doc.get("productOrderItem") or doc.get("orderItem") or []:
        offering = item.get("productOffering") or {}
        if offering.get("id"):
            return offering["id"]
    return None


def _order_columns(doc: dict) -> dict:
    return {
        "state": doc.get("state"),
        "customer_id": _related_party_id(doc),
        "offering_id": _first_offering_id(doc),
    }


def _product_columns(doc: dict) -> dict:
    order_id = None
    for ref in doc.get("productOrderItem") or []:
        if ref.get("id"):
            order_id = ref["id"]
            break
    offering = doc.get("productOffering") or {}
    return {
        "name": doc.get("name"),
        "status": doc.get("status"),
        "order_id": order_id,
        "customer_id": _related_party_id(doc),
        "offering_id": offering.get("id"),
    }


# ---------------------------------------------------------------------------
# The stores — drop-in replacements for the old in-memory dicts.
# ---------------------------------------------------------------------------

individuals = Store(models.Individual, _individual_columns)
organisations = Store(models.Organisation, _organisation_columns)
customers = Store(models.Customer, _customer_columns)
billing_accounts = Store(models.BillingAccount, _billing_account_columns)
product_specifications = Store(models.ProductSpecification, _spec_columns)
product_offerings = Store(models.ProductOffering, _offering_columns)
product_orders = Store(models.ProductOrder, _order_columns)
product_inventory = Store(models.Product, _product_columns)


# --- TMF700 Shipment ---

def _shipment_columns(doc: dict) -> dict:
    return {
        "status": doc.get("status"),
        "order_id": doc.get("productOrder", {}).get("id") if doc.get("productOrder") else None,
        "tracking_number": doc.get("trackingNumber"),
    }


shipments = Store(models.Shipment, _shipment_columns)


# --- TMF641 Service Order ---

def _service_order_columns(doc: dict) -> dict:
    return {
        "state": doc.get("state"),
        "order_id": doc.get("productOrder", {}).get("id") if doc.get("productOrder") else None,
    }


service_orders = Store(models.ServiceOrder, _service_order_columns)


# --- TMF638 Service Inventory ---

def _service_columns(doc: dict) -> dict:
    return {
        "name": doc.get("name"),
        "state": doc.get("state"),
        "order_id": doc.get("productOrder", {}).get("id") if doc.get("productOrder") else None,
        "customer_id": _related_party_id(doc),
    }


services = Store(models.Service, _service_columns)


# --- TMF678 Customer Bill ---

def _customer_bill_columns(doc: dict) -> dict:
    ba = doc.get("billingAccount") or {}
    return {
        "state": doc.get("state"),
        "billing_account_id": ba.get("id"),
        "order_id": doc.get("productOrder", {}).get("id") if doc.get("productOrder") else None,
    }


customer_bills = Store(models.CustomerBill, _customer_bill_columns)
