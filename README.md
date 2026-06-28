# TMF BSS Showcase

A **TM Forum Open API–compliant** Business Support Systems stack built with Python + FastAPI.

Designed as a portfolio project demonstrating BSS domain knowledge and TMF API specification fluency.

**Live demo:** [https://tmf-bss-showcase-01.onrender.com/docs](https://tmf-bss-showcase-01.onrender.com/docs)

---

## What this demonstrates

| API | Domain | Endpoints | What it does |
|-----|--------|-----------|--------------|
| **TMF632** | Party Management | 5 | Create, retrieve, update, and delete customer contacts |
| **TMF620** | Product Catalog | 10 | Browse product specifications, offerings, and pricing |
| **TMF622** | Product Ordering | 5 | Place orders with automatic fulfilment state machine |
| **TMF688** | Event Management | 5 | Query events, view stats, register subscriptions |

**Total: 26 endpoints** — all TMF-specification-compliant, all live.

All data is stubbed in-memory — no external systems are called.  Orders automatically
advance `acknowledged → inProgress → completed` via a background task, demonstrating
understanding of BSS fulfilment process flows.

---

## Demo walkthrough

All commands run against the live URL.

```bash
BASE=https://tmf-bss-showcase-01.onrender.com

# 1. Health check
curl -s $BASE/health | jq .

# 2. Create a contact (TMF632 Individual)
curl -s -X POST $BASE/party/v5/individual \
  -H "Content-Type: application/json" \
  -d '{
    "fullName": "Ajay Kumar",
    "givenName": "Ajay",
    "familyName": "Kumar",
    "contactMedium": [{
      "mediumType": "email",
      "preferred": true,
      "characteristic": {"emailAddress": "ajay@example.com"}
    }],
    "partyCharacteristic": [{"name": "loyaltyTier", "value": "Gold"}]
  }' | jq .

# 3. Browse product offerings (TMF620 — 3 pre-seeded)
curl -s $BASE/productCatalog/v4/productOffering | jq .

# 4. Browse product specifications
curl -s $BASE/productCatalog/v4/productSpecification | jq .

# 5. Place a product order (TMF622)
curl -s -X POST $BASE/productOrderingManagement/v4/productOrder \
  -H "Content-Type: application/json" \
  -d '{
    "description": "New 5G plan order",
    "externalId": "CRM-2026-0042",
    "relatedParty": [{"id": "party-001", "name": "Ajay Kumar", "role": "customer"}],
    "orderItem": [{
      "id": "1",
      "quantity": 1,
      "action": "add",
      "productOffering": {"id": "offering-5g-unlimited", "name": "Mobile 5G Unlimited"}
    }],
    "note": [{"author": "Sales Agent", "text": "VIP customer - expedite"}]
  }' | jq .

# 6. Poll order state (save the id from step 5) — wait 3s for inProgress, 8s for completed
curl -s $BASE/productOrderingManagement/v4/productOrder/<ORDER_ID> | jq '{id, state, completionDate}'

# 7. Event log — see all domain events
curl -s $BASE/hub | jq .

# 8. Filter events by type
curl -s "$BASE/hub?eventType=ProductOrderStateChangeEvent" | jq .

# 9. Filter events by domain
curl -s "$BASE/hub?domain=order" | jq .

# 10. Event statistics
curl -s $BASE/hub/stats | jq .
```

---

## Architecture

```
main.py               ← single FastAPI app, mounts all routers
├── services/party/   ← TMF632 Individual CRUD + events
├── services/catalog/ ← TMF620 ProductSpec & ProductOffering CRUD + seed data
├── services/order/   ← TMF622 ProductOrder + background state machine
└── shared/
    ├── store.py      ← in-memory dicts (no database needed)
    ├── events.py     ← TMF688 event bus with filtering + subscriptions
    └── schemas/      ← Pydantic models matching TMF JSON wire format
        ├── tmf632.py
        ├── tmf620.py
        └── tmf622.py
```

### Key design decisions

- **Single process, single app** — no inter-service networking; all routers share the same in-memory store
- **Pydantic models with camelCase aliases** — Python code uses snake_case; JSON wire format matches TMF specs exactly
- **Background task state machine** — orders auto-advance through fulfilment states with real delays
- **Event-driven** — every mutation publishes a TMF688-style event with eventId, correlationId, and domain tagging
- **Seeded catalog** — 3 product specifications and 3 offerings load on startup so the API is never empty

---

## Run locally

```bash
git clone https://github.com/allmylearningoeshere/tmf-bss-showcase-01
cd tmf-bss-showcase-01
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt && pip install -e .
python -m uvicorn main:app --reload
# → http://localhost:8000/docs
```

---

## Deploy to Render

1. Push to GitHub
2. New Web Service → connect repo → Render detects `render.yaml`
3. Set env var `PYTHON_VERSION=3.11.0` in the Render dashboard
4. Deploy — live URL appears in the dashboard

---

## Tech stack

- **Python 3.11** + **FastAPI** + **Pydantic v2**
- **Uvicorn** ASGI server
- **Render** cloud hosting (free tier)
- **Swagger UI** auto-generated API documentation
