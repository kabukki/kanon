import logging
from datetime import date

import httpx

from app.config import settings
from app.errors import UpstreamUnavailableError
from app.models import (
    Coordinates,
    DailyForecast,
    TemperatureUnit,
    WeatherCondition,
    WeatherReading,
)

log = logging.getLogger(__name__)

# Mapping from upstream provider's condition strings to our enum.
_CONDITION_MAP = {
    "clear": WeatherCondition.SUN,
    "sunny": WeatherCondition.SUN,
    "cloudy": WeatherCondition.CLOUD,
    "overcast": WeatherCondition.CLOUD,
    "rain": WeatherCondition.RAIN,
    "drizzle": WeatherCondition.RAIN,
    "snow": WeatherCondition.SNOW,
    "sleet": WeatherCondition.SNOW,
    "thunder": WeatherCondition.THUNDER,
    "thunderstorm": WeatherCondition.THUNDER,
}


def _map_condition(raw: str) -> WeatherCondition:
    return _CONDITION_MAP.get(raw.lower(), WeatherCondition.CLOUD)


def _convert_temp(celsius: float, unit: TemperatureUnit) -> float:
    if unit == "farenheit":
        return round(celsius * 9 / 5 + 32, 1)
    return round(celsius, 1)


class FictionalWeatherClient:
    def __init__(self, client: httpx.AsyncClient, api_key: str, base_url: str):
        self._client = client
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}"}

    async def current(self, coords: Coordinates, unit: TemperatureUnit) -> WeatherReading:
        try:
            r = await self._client.get(
                f"{self._base_url}/v1/current",
                params={"lat": coords.lat, "lng": coords.lng},
                headers=self._headers(),
            )
            r.raise_for_status()
        except httpx.HTTPError as e:
            log.warning("fictional weather error: %s", e)
            raise UpstreamUnavailableError("Weather provider unavailable")

        data = r.json()
        return WeatherReading(
            weather=_map_condition(data["condition"]),
            temperature=_convert_temp(float(data["temperature_c"]), unit),
            unit=unit,
        )

    async def forecast(
        self,
        coords: Coordinates,
        unit: TemperatureUnit,
        anchor: date,
        days: int = 7,
    ) -> list[DailyForecast]:
        try:
            r = await self._client.get(
                f"{self._base_url}/v1/forecast",
                params={
                    "lat": coords.lat,
                    "lng": coords.lng,
                    "from": anchor.isoformat(),
                    "days": days,
                },
                headers=self._headers(),
            )
            r.raise_for_status()
        except httpx.HTTPError as e:
            log.warning("fictional weather error: %s", e)
            raise UpstreamUnavailableError("Weather provider unavailable")

        payload = r.json()
        out: list[DailyForecast] = []
        for d in payload.get("days", [])[:days]:
            out.append(
                DailyForecast(
                    date=date.fromisoformat(d["date"]),
                    weather=_map_condition(d["condition"]),
                    temperature=_convert_temp(float(d["temperature_c"]), unit),
                    unit=unit,
                )
            )
        return out
