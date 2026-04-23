import httpx
import pytest

from app import cache as cache_mod
from app.clients.fictional_weather import FictionalWeatherClient
from app.clients.mapbox import MapboxClient
from app.errors import UpstreamUnavailableError
from app.models import Coordinates
from app.service import WeatherService


class _StubTransport(httpx.AsyncBaseTransport):
    def __init__(self, handler):
        self._handler = handler

    async def handle_async_request(self, request):
        return self._handler(request)


def _make_client(handler):
    return httpx.AsyncClient(transport=_StubTransport(handler))


async def test_current_by_coords_success():
    def handler(req: httpx.Request) -> httpx.Response:
        assert "/v1/current" in req.url.path
        return httpx.Response(200, json={"condition": "sunny", "temperature_c": 20.0})

    async with _make_client(handler) as http:
        svc = WeatherService(
            FictionalWeatherClient(http, "k", "http://upstream"),
            MapboxClient(http, "t", "http://mapbox"),
        )
        resp = await svc.current(None, 48.85, 2.35, "celsius")

    assert resp.weather == "sun"
    assert resp.temperature == 20.0
    assert resp.location == Coordinates(lat=48.85, lng=2.35)


async def test_farenheit_conversion():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"condition": "clear", "temperature_c": 0.0})

    async with _make_client(handler) as http:
        svc = WeatherService(
            FictionalWeatherClient(http, "k", "http://upstream"),
            MapboxClient(http, "t", "http://mapbox"),
        )
        resp = await svc.current(None, 0, 0, "farenheit")

    assert resp.unit == "farenheit"
    assert resp.temperature == 32.0


async def test_upstream_down_serves_stale():
    calls = {"n": 0}

    def handler(req: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(200, json={"condition": "rain", "temperature_c": 12.0})
        return httpx.Response(503)

    async with _make_client(handler) as http:
        svc = WeatherService(
            FictionalWeatherClient(http, "k", "http://upstream"),
            MapboxClient(http, "t", "http://mapbox"),
        )
        first = await svc.current(None, 1.0, 2.0, "celsius")
        # Invalidate the fresh cache entry but keep the stale fallback.
        await cache_mod.cache._client.delete("current:1.000:2.000:celsius")
        second = await svc.current(None, 1.0, 2.0, "celsius")

    assert first.weather == "rain"
    assert second.weather == "rain"
    assert second.stale is True


async def test_upstream_down_no_stale_raises():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    async with _make_client(handler) as http:
        svc = WeatherService(
            FictionalWeatherClient(http, "k", "http://upstream"),
            MapboxClient(http, "t", "http://mapbox"),
        )
        with pytest.raises(UpstreamUnavailableError):
            await svc.current(None, 3.0, 4.0, "celsius")


async def test_forecast_returns_7_days():
    days_payload = [
        {"date": f"2026-04-{23 + i:02d}", "condition": "cloudy", "temperature_c": 15 + i}
        for i in range(7)
    ]

    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"days": days_payload})

    async with _make_client(handler) as http:
        svc = WeatherService(
            FictionalWeatherClient(http, "k", "http://upstream"),
            MapboxClient(http, "t", "http://mapbox"),
        )
        resp = await svc.forecast(None, 10.0, 20.0, "celsius", None)

    assert len(resp.days) == 7
    assert resp.days[0].weather == "cloud"
