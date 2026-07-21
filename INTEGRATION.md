# Address Lookup — backend integration

This adds a `GET /addressLookup/v1/streets` endpoint that proxies to the free,
keyless OpenPLZ API and returns the streets in a German postcode. The Odyssey
storefront's "Lookup" button calls it.

## 1. Add the router file

Place the folder in your backend repo so the path is exactly:

```
services\address_lookup\__init__.py
```

(Same level as `services\customer`, `services\inventory`, etc.)

## 2. Ensure httpx is installed

The proxy uses `httpx` for the async HTTP call. FastAPI usually pulls it in via
`starlette`/`TestClient`, but add it explicitly to be safe. In `requirements.txt`:

```
httpx
```

Then, locally:

```powershell
pip install httpx --break-system-packages
```

(On Render, the redeploy installs from `requirements.txt` automatically.)

## 3. Mount the router in main.py

Add the import alongside the others:

```python
from services.address_lookup import router as address_lookup_router
```

And mount it alongside the others:

```python
app.include_router(address_lookup_router)
```

## 4. Verify locally before pushing

From the backend repo root:

```powershell
python -c "from main import app; print([r.path for r in app.routes if 'addressLookup' in r.path])"
```

Expected output:

```
['/addressLookup/v1/streets']
```

## 5. Push

```powershell
git add .; git commit -m "Add OpenPLZ address lookup proxy (GET /addressLookup/v1/streets)"; git push
```

Reload `/docs` — you should see the **Address Lookup (OpenPLZ proxy)** tag with
the streets endpoint. Try it with `postalCode=10115` (Berlin) to confirm.

## Notes

- **No API key.** OpenPLZ is public and keyless — nothing to configure.
- **CORS.** The browser only ever calls your backend, which already has
  `CORSMiddleware`, so no extra CORS work is needed for OpenPLZ.
- **Timeouts.** OpenPLZ can be slow on a cold call; the proxy uses a 10s timeout
  and returns a clean 504/502 with a friendly message that the UI surfaces.
- **Events.** Each lookup publishes an `AddressLookupEvent` to your event bus,
  so it shows up in the TMF688 event feed like everything else.
