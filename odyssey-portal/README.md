# Odyssey Portal

A guided, consumer-facing SIM-only order journey — the storefront companion to
the [TMF BSS showcase](https://github.com/allmylearningoeshere/tmf-bss-showcase-01).
Built with React + Vite, deployed as a Render Static Site.

The flow mirrors an Apple-style vertical checkout: choose a plan → enter details
→ review → watch the order fulfil in real time → confirmation. Behind the scenes
it drives the full TMF customer-to-order lifecycle against the live backend.

## The order journey → TMF API mapping

| Stage | What happens | TMF API |
|---|---|---|
| 1 · Plan | Fetch and render sellable offerings | TMF620 Product Catalog |
| 2 · Details | Collected in state (Germany fixed, +49 prefix) | — |
| 3 · Review | Summary of plan + delivery | — |
| 4 · Processing | `POST` party → customer → billing account → order | TMF632 · 629 · 666 · 622 |
| 4 · Tracker | Poll order `acknowledged → inProgress → completed` | TMF622 |
| 5 · Done | Show order ref + auto-created inventory ref | TMF637 Product Inventory |

## Local development

```powershell
npm install; npm run dev
```

Opens at `http://localhost:5173`. By default it calls the public Render backend.
To point elsewhere, copy `.env.example` to `.env` and edit `VITE_API_BASE_URL`.

```powershell
copy .env.example .env
```

## Build

```powershell
npm run build; npm run preview
```

The production bundle lands in `dist/`.

## Deploy to Render

1. Push this repo to GitHub.
2. In Render: **New → Static Site → connect the repo**. Render auto-detects
   `render.yaml` (build `npm install && npm run build`, publish `./dist`).
3. Confirm the `VITE_API_BASE_URL` env var points at your backend.
4. Deploy. Every push to the default branch auto-redeploys.

The SPA rewrite rule in `render.yaml` routes all paths to `index.html` so the
app works on refresh and deep links.

## Notes on the free tier

The backend sleeps after ~15 minutes idle and takes up to a minute to wake.
The plan screen shows a friendly retry message if the first catalogue call
times out — reload once the backend is up. Order and inventory references live
in the backend's in-memory store, so they reset when the backend restarts.

## Configuration

| Env var | Purpose | Default |
|---|---|---|
| `VITE_API_BASE_URL` | Base URL of the TMF BSS backend | Public Render deployment |
