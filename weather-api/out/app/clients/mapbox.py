import logging
from urllib.parse import quote

import httpx

from app.config import settings
from app.errors import NotFoundError, UpstreamUnavailableError
from app.models import Coordinates

log = logging.getLogger(__name__)


class MapboxClient:
    def __init__(self, client: httpx.AsyncClient, token: str, base_url: str):
        self._client = client
        self._token = token
        self._base_url = base_url.rstrip("/")

    async def geocode(self, city: str) -> tuple[Coordinates, str]:
        """Return (coordinates, resolved_place_name) for the given city."""
        path = f"/geocoding/v5/mapbox.places/{quote(city)}.json"
        params = {"access_token": self._token, "limit": 1, "types": "place"}
        try:
            r = await self._client.get(f"{self._base_url}{path}", params=params)
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise NotFoundError(f"City '{city}' not found", code="city_not_found")
            log.warning("mapbox http error: %s", e)
            raise UpstreamUnavailableError("Geocoding service unavailable")
        except httpx.HTTPError as e:
            log.warning("mapbox network error: %s", e)
            raise UpstreamUnavailableError("Geocoding service unavailable")

        data = r.json()
        features = data.get("features") or []
        if not features:
            raise NotFoundError(f"City '{city}' not found", code="city_not_found")
        feat = features[0]
        lng, lat = feat["center"]
        return Coordinates(lat=lat, lng=lng), feat.get("place_name", city)
