# TMF BSS Showcase

A TM Forum Open API–compliant Business Support Systems stack built with **Python + FastAPI**.  
Designed as a portfolio project demonstrating BSS domain knowledge and TMF API specification fluency.

**Live demo:** `https://your-app.onrender.com/docs`

---

## What this demonstrates

| API | Domain | Endpoints |
|-----|--------|-----------|
| TMF632 | Party Management | Create / retrieve individuals and organisations |
| TMF620 | Product Catalog | Browse product offerings and specifications |
| TMF622 | Product Ordering | Place orders; watch state machine advance automatically |

All data is stubbed — no external systems are called.  Orders automatically
advance `acknowledged → inProgress → completed` via a background task,
demonstrating understanding of BSS fulfilment process flows.

---

## Demo walkthrough

All commands run against the live URL.  Replace `BASE` with your deployed host.

```bash
BASE=https://your-app.onrender.com

# 1. Confirm the service is healthy
curl $BASE/health

# 2. Create a contact (TMF632 Individual)
curl -s -X POST $BASE/party/v5/individual \
  -H "Content-Type: application/json" \
  -d '{
    "fullName": "Ajay Kumar",
    "contactMedium": [{"mediumType": "email", "characteristic": {"emailAddress": "ajay@example.com"}}]
  }' | jq .

# 3. Browse product offerings (TMF620) — seeded on startup
curl -s $BASE/productCatalog/v4/productOffering | jq .

# 4. Place a product order (TMF622)
curl -s -X POST $BASE/productOrderingManagement/v4/productOrder \
  -H "Content-Type: application/json" \
  -d '{
    "description": "New mobile plan order",
    "orderItem": [{"id": "1", "quantity": 1, "action": "add",
      "productOffering": {"id": "offering-001", "name": "Mobile 5G Plan"}}]
  }' | jq .

# 5. Poll the order — state advances automatically (save the id from step 4)
curl -s $BASE/productOrderingManagement/v4/productOrder/<ORDER_ID> | jq .state

# 6. Inspect the event log (TMF688-style hub)
curl -s $BASE/hub | jq .
```

A `demo.sh` script that runs the full sequence automatically is included.

---

## Run locally

```bash
git clone https://github.com/your-handle/tmf-bss-showcase
cd tmf-bss-showcase
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
# → http://localhost:8000/docs
```

---

## Deploy

### Render (recommended — free tier)
1. Push to GitHub
2. New Web Service → connect repo → Render auto-detects `render.yaml`
3. Deploy — your live URL appears in the dashboard

### Railway
1. Push to GitHub  
2. New Project → Deploy from GitHub → select repo  
3. `railway.json` is picked up automatically

### Fly.io
```bash
fly launch   # reads fly.toml
fly deploy
```

---

## Architecture

```
main.py               ← single FastAPI app, mounts all routers
├── services/party    ← TMF632 router
├── services/catalog  ← TMF620 router
├── services/order    ← TMF622 router + state machine background task
└── shared/
    ├── store.py      ← in-memory dicts (no database needed)
    └── events.py     ← lightweight pub/sub event bus
```

---

## Roadmap

- [ ] Sprint 2 — TMF632 Party Management (full CRUD)  
- [ ] Sprint 3 — TMF620 Product Catalog (offerings, specs, pricing)  
- [ ] Sprint 4 — TMF622 Product Ordering + state machine  
- [ ] Sprint 5 — TMF688-style event notifications  
- [ ] Sprint 6 — Polish, demo script, tagged release  

Future phases: TMF637 Product Inventory · TMF678 Customer Bill · TMF666 Account · TMF621 Trouble Ticket
