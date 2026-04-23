from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import ValidationError

from app.deps import WeatherServiceDep
from app.errors import BadRequestError
from app.models import (
    CurrentWeatherResponse,
    ForecastQuery,
    ForecastResponse,
    TemperatureUnit,
    WeatherQuery,
)

router = APIRouter(prefix="/weather", tags=["weather"])


def _parse_query(
    city: str | None,
    lat: float | None,
    lng: float | None,
    unit: TemperatureUnit,
) -> WeatherQuery:
    try:
        return WeatherQuery(city=city, lat=lat, lng=lng, unit=unit)
    except ValidationError as e:
        raise BadRequestError(str(e), code="invalid_query")


@router.get("/current", response_model=CurrentWeatherResponse)
async def get_current(
    service: WeatherServiceDep,
    city: Annotated[str | None, Query(max_length=200)] = None,
    lat: Annotated[float | None, Query(ge=-90, le=90)] = None,
    lng: Annotated[float | None, Query(ge=-180, le=180)] = None,
    unit: Annotated[TemperatureUnit, Query()] = "celsius",
):
    q = _parse_query(city, lat, lng, unit)
    return await service.current(q.city, q.lat, q.lng, q.unit)


@router.get("/forecast", response_model=ForecastResponse)
async def get_forecast(
    service: WeatherServiceDep,
    city: Annotated[str | None, Query(max_length=200)] = None,
    lat: Annotated[float | None, Query(ge=-90, le=90)] = None,
    lng: Annotated[float | None, Query(ge=-180, le=180)] = None,
    unit: Annotated[TemperatureUnit, Query()] = "celsius",
    anchor_date: Annotated[date | None, Query()] = None,
):
    try:
        q = ForecastQuery(city=city, lat=lat, lng=lng, unit=unit, anchor_date=anchor_date)
    except ValidationError as e:
        raise BadRequestError(str(e), code="invalid_query")
    return await service.forecast(q.city, q.lat, q.lng, q.unit, q.anchor_date)
