import logging
from datetime import date, datetime, timezone

from app.cache import cache
from app.clients.fictional_weather import FictionalWeatherClient
from app.clients.mapbox import MapboxClient
from app.config import settings
from app.errors import UpstreamUnavailableError
from app.models import (
    Coordinates,
    CurrentWeatherResponse,
    DailyForecast,
    ForecastResponse,
    TemperatureUnit,
    WeatherCondition,
)

log = logging.getLogger(__name__)


class WeatherService:
    def __init__(self, weather: FictionalWeatherClient, mapbox: MapboxClient):
        self._weather = weather
        self._mapbox = mapbox

    async def _resolve(
        self, city: str | None, lat: float | None, lng: float | None
    ) -> tuple[Coordinates, str | None]:
        if city is not None:
            key = f"geo:{city.lower().strip()}"
            cached = await cache.get_json(key)
            if cached:
                return Coordinates(**cached["coords"]), cached.get("place_name")
            coords, place_name = await self._mapbox.geocode(city)
            await cache.set_json(
                key,
                {"coords": coords.model_dump(), "place_name": place_name},
                ttl=settings.cache_ttl_geocode_seconds,
            )
            return coords, place_name
        assert lat is not None and lng is not None
        return Coordinates(lat=lat, lng=lng), None

    async def current(
        self,
        city: str | None,
        lat: float | None,
        lng: float | None,
        unit: TemperatureUnit,
    ) -> CurrentWeatherResponse:
        coords, place_name = await self._resolve(city, lat, lng)
        cache_key = f"current:{coords.lat:.3f}:{coords.lng:.3f}:{unit}"

        cached = await cache.get_json(cache_key)
        if cached:
            return CurrentWeatherResponse(**cached)

        try:
            reading = await self._weather.current(coords, unit)
        except UpstreamUnavailableError:
            stale = await cache.get_stale(cache_key)
            if stale:
                log.info("serving stale current weather for %s", cache_key)
                return CurrentWeatherResponse(**{**stale, "stale": True})
            raise

        resp = CurrentWeatherResponse(
            weather=reading.weather,
            temperature=reading.temperature,
            unit=reading.unit,
            location=coords,
            resolved_city=place_name,
        )
        payload = resp.model_dump()
        await cache.set_json(cache_key, payload, ttl=settings.cache_ttl_current_seconds)
        await cache.set_stale(cache_key, payload)
        return resp

    async def forecast(
        self,
        city: str | None,
        lat: float | None,
        lng: float | None,
        unit: TemperatureUnit,
        anchor: date | None,
    ) -> ForecastResponse:
        coords, place_name = await self._resolve(city, lat, lng)
        anchor_date = anchor or datetime.now(timezone.utc).date()
        cache_key = f"forecast:{coords.lat:.3f}:{coords.lng:.3f}:{unit}:{anchor_date.isoformat()}"

        cached = await cache.get_json(cache_key)
        if cached:
            return ForecastResponse(**cached)

        try:
            days = await self._weather.forecast(coords, unit, anchor_date, days=7)
        except UpstreamUnavailableError:
            stale = await cache.get_stale(cache_key)
            if stale:
                log.info("serving stale forecast for %s", cache_key)
                return ForecastResponse(**{**stale, "stale": True})
            raise

        resp = ForecastResponse(
            location=coords,
            resolved_city=place_name,
            days=days,
        )
        payload = resp.model_dump()
        await cache.set_json(cache_key, payload, ttl=settings.cache_ttl_forecast_seconds)
        await cache.set_stale(cache_key, payload)
        return resp
