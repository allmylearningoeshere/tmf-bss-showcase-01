# Phase 1 — Persistence Layer

Moves every TMF entity from in-memory Python dicts into Neon Postgres, so data
survives restarts and orders stay retrievable indefinitely.

## What changed, in one sentence

`shared/store.py` no longer holds dicts — it re-exports database-backed `Store`
objects that expose the **same dict interface** (`store[id] = rec`, `.get()`,
`.values()`, `.pop()`), so the service routers kept working with almost no
changes to their logic.

---

## 1. Files to place

### New — the database package

```
shared\db\__init__.py
shared\db\session.py
shared\db\models.py
shared\db\repository.py
```

### New — Alembic migrations

```
alembic.ini
alembic\env.py
alembic\script.py.mako
alembic\README
alembic\versions\83f9f9793ba4_initial_tmf_entity_schema.py
```

### Replaced

```
shared\store.py                  now re-exports the DB-backed stores
main.py                          adds a startup hook (init tables + seed)
requirements.txt                 adds SQLAlchemy, psycopg2-binary, alembic
services\catalog\seed.py         seeding is now idempotent + deferred
services\catalog\__init__.py     no longer seeds on import
services\party\__init__.py       save-back after PATCH
services\customer\__init__.py    save-back after PATCH
services\account\__init__.py     save-back after PATCH
services\inventory\__init__.py   save-back after PATCH
services\order\__init__.py       save-backs after state transitions + PATCH
```

The simplest approach is to unzip over your backend repo root and let it
overwrite.

---

## 2. Why the "save-back" edits were necessary

The old code mutated records in place:

```python
record = product_orders.get(order_id)
record["state"] = "inProgress"        # worked: same dict object in memory
```

With a database, that change lives only in a local copy and is silently lost.
Every mutation site now writes the record back:

```python
record["state"] = "inProgress"
product_orders[order_id] = record     # persists the transition
```

There are nine of these across six files. They are the only substantive logic
changes in the whole migration.

---

## 3. Deploy

Nothing to configure — `DATABASE_URL` is already set on Render from Phase 0.

```powershell
git add .; git commit -m "Phase 1: persist TMF entities in Postgres"; git push
```

On boot the app creates any missing tables and seeds the catalogue **only if it
is empty**, so restarts are cheap and existing data is never overwritten.

### Optional: verify locally first

```powershell
pip install -r requirements.txt
python -c "from main import app; print('imports OK')"
```

Without `DATABASE_URL` set, the app falls back to a local SQLite file
(`local_dev.db`), so you can run it locally without touching Neon.

---

## 4. Verifying it worked

After the deploy goes green:

1. Open `/docs` and place an order through Odyssey as usual.
2. In the Render dashboard, **restart the backend service manually**.
3. Retrieve that same order — `GET /productOrderingManagement/v4/productOrder/{id}`.

Previously this returned 404 after a restart. It now returns the order with its
final state, and the correlated inventory product is still there.

You can also inspect the data directly in Neon's SQL editor:

```sql
select id, state, customer_id, offering_id, created_at
from product_orders order by created_at desc limit 10;

-- walk the full correlation chain for one order
select o.id as order_id, o.state,
       c.name as customer, i.full_name as party, i.email,
       p.id as product_id, p.status as product_status
from product_orders o
left join customers c        on c.id = o.customer_id
left join individuals i      on i.id = c.party_id
left join products p         on p.order_id = o.id
order by o.created_at desc limit 10;
```

---

## 5. The schema

Hybrid design — typed columns for anything queryable, plus a `JSONB` `doc`
column holding the complete TMF resource verbatim. Reads serve `doc` straight
back, so the API contract is byte-for-byte unchanged.

```
individuals ──< customers ──< billing_accounts
                    │
                    └──< product_orders ──< products (inventory)

product_offerings, product_specifications, organisations, events
```

The foreign keys are what make the lifecycle traceable and power the retrieve
screens in Phase 4.

---

## 6. Using Alembic (optional)

The app calls `create_all()` on startup, which is enough to get running. Alembic
is included for versioned schema changes going forward.

```powershell
# after editing shared\db\models.py
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

`alembic\env.py` reads `DATABASE_URL` from the environment, so no credentials
are ever written to `alembic.ini`.

---

## 7. What was tested

Verified against a real uvicorn server (not just TestClient), on both a
`create_all` database and an Alembic-migrated one:

- Full lifecycle persists: party → customer → billing account → order
- Order state machine transitions correctly and **each transition is written to
  the database**: `acknowledged` (3s) → `inProgress` (5s) → `completed`
- Inventory auto-creates on completion, correlated to its order
- **Server killed and restarted against the same database** — order survived
  with its final state, inventory survived still linked to that order
- Catalogue stayed at 3 offerings across restarts rather than re-seeding to 6
- Correlation chain walks cleanly: order → customer → individual, with accounts
  and products linked by foreign key

---

## 8. Note on Neon's scale-to-zero

Neon suspends compute after idle and resumes on the next query. The engine is
configured with `pool_pre_ping=True` and a 300-second `pool_recycle`, so
connections dropped during a suspend are discarded and reopened transparently.
The first request after a long idle may take a few hundred milliseconds extra —
imperceptible behind your always-on Render backend.
