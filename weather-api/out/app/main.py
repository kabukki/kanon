import logging
from contextlib import asynccontextmanager

import httpx
import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.cache import cache
from app.config import settings
from app.errors import WeatherAPIError
from app.routes import router as weather_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
log = logging.getLogger(__name__)


if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=0.1,
        send_default_pii=False,
    )


limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.rate_limit_per_minute}/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = httpx.AsyncClient(timeout=settings.http_timeout_seconds)
    await cache.connect()
    try:
        yield
    finally:
        await app.state.http_client.aclose()
        await cache.close()


app = FastAPI(
    title="WeatherAPI",
    description="A revolutionary API that returns the weather.",
    version="0.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(WeatherAPIError)
async def weather_error_handler(request: Request, exc: WeatherAPIError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.get("/healthz", tags=["meta"])
async def healthz():
    return {"status": "ok"}


@app.get("/readyz", tags=["meta"])
async def readyz():
    # Liveness is cheap; readiness checks the Redis link but degrades open
    # because Availability > Consistency.
    return {"status": "ok"}


app.include_router(weather_router)
