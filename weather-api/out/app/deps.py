from typing import Annotated

import httpx
from fastapi import Depends, Request

from app.clients.fictional_weather import FictionalWeatherClient
from app.clients.mapbox import MapboxClient
from app.config import settings
from app.service import WeatherService


def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_client


def get_weather_service(
    client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
) -> WeatherService:
    weather = FictionalWeatherClient(
        client,
        api_key=settings.fictional_weather_api_key,
        base_url=settings.fictional_weather_api_base_url,
    )
    mapbox = MapboxClient(
        client,
        token=settings.mapbox_token,
        base_url=settings.mapbox_base_url,
    )
    return WeatherService(weather, mapbox)


WeatherServiceDep = Annotated[WeatherService, Depends(get_weather_service)]
