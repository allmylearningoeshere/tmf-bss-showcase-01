# Phase 4 — Retrieve Screens

Adds a "Track your order" surface to the Odyssey portal, so an order placed
days ago can be looked up cleanly — the visible payoff of the Phase 1
persistence work.

## IMPORTANT — how to apply these files

Extract this zip **into** your existing `odyssey-portal` folder so the files
merge. Do NOT rename the old `src` folder and paste this one in its place —
that would drop the untouched files. (This is the trap from the Phase 1 deploy.)
Each file below simply overwrites or adds at its path.

## Files

| File | Action |
|------|--------|
| `src/components/RetrieveView.jsx` | **New** — the retrieve screen |
| `src/App.jsx` | Replace — adds view toggle + track link |
| `src/lib/api.js` | Replace — adds `getProduct(id)` |
| `src/styles.css` | Replace — tabs, badges, search styles |

## What it does

On the landing (plan) screen there's now a **"Already ordered? Track your
order"** link. It opens a retrieve view with two tabs:

- **Find order** — enter an order reference. Shows the order (status, plan,
  dates) and, by walking the correlation, the product it provisioned.
- **Find product** — enter a product reference. Shows the product directly.

All lookups hit the now-persistent backend, so references resolve even long
after the order was placed and after backend restarts.

## Endpoints used

- `GET /productOrderingManagement/v4/productOrder/{id}` (TMF622)
- `GET /productInventory/v4/product` and `/product/{id}` (TMF637)

No backend changes — these endpoints already exist and now read from Postgres.

## Deploy

```powershell
git add .; git commit -m "Phase 4: retrieve screens for order and product lookup"; git push
```

Render redeploys the static site automatically. Hard-refresh (Ctrl+F5) once live.

## Test

1. Place an order; note the order reference from the confirmation screen.
2. Go back to the landing screen → "Track your order" → Find order tab.
3. Paste the reference → Search. The order and its product should appear.
4. For the strongest showcase: restart the backend in Render first, then look
   the order up — it still resolves, proving persistence end to end.
