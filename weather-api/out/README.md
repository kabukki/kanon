# WeatherAPI

Revolutionary weather web service. FastAPI + Redis, deployed on Cloud Run (europe-west9).

## Endpoints

- `GET /weather/current?city=Paris&unit=celsius`
- `GET /weather/current?lat=48.85&lng=2.35`
- `GET /weather/forecast?city=Paris&anchor_date=2026-04-23`
- `GET /healthz`, `GET /readyz`

Either `city` or (`lat`,`lng`) — never both. `unit` is `celsius` (default) or `farenheit`.

## Run locally

```bash
uv sync
cp .env.example .env      # fill secrets
uv run uvicorn app.main:app --reload
```

Tests: `uv run pytest`.

## Deploy

```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/weather-api
gcloud run services replace deploy/cloudrun.yaml --region=europe-west9
gcloud run domain-mappings create --service=weather-api --domain=weather.example.com --region=europe-west9
```

## Design notes

- **Cache (Redis):** keyed by coords+unit. Two copies written — one with TTL (fresh), one without (stale fallback). On upstream outage we serve stale with `"stale": true`, honoring *availability > consistency*.
- **Rate limit:** 60 req/min/IP via slowapi.
- **Errors:** `400` bad input, `404` unknown city, `503` upstream unavailable with no stale fallback, `500` otherwise. Body shape: `{"error": {"code", "message"}}`.
- **Observability:** Sentry initialized when `SENTRY_DSN` is set, 10% trace sampling. `send_default_pii=False` for GDPR.
- **GDPR:** no logging of IPs or query params; no persistence of user data.
- **Budget ($10/mo):** Cloud Run scales to zero, `minScale=0`, 256 MiB / 1 vCPU, concurrency 80. Redis: use Upstash free tier or Memorystore Basic 1 GiB (~$5/mo). Mapbox/FictionalWeather stay on free tiers at 10 req/s given the 30-day geocode cache.
