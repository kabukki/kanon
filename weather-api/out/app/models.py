from datetime import date
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class WeatherCondition(str, Enum):
    SUN = "sun"
    CLOUD = "cloud"
    RAIN = "rain"
    SNOW = "snow"
    THUNDER = "thunder"


TemperatureUnit = Literal["celsius", "farenheit"]


class Coordinates(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class WeatherQuery(BaseModel):
    city: str | None = None
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    unit: TemperatureUnit = "celsius"

    @model_validator(mode="after")
    def validate_location(self) -> "WeatherQuery":
        has_city = self.city is not None and self.city.strip() != ""
        has_coords = self.lat is not None and self.lng is not None
        has_partial_coords = (self.lat is None) != (self.lng is None)

        if has_city and has_coords:
            raise ValueError("Provide either 'city' or 'lat'/'lng', not both")
        if not has_city and not has_coords:
            raise ValueError("Provide either 'city' or 'lat'/'lng'")
        if has_partial_coords:
            raise ValueError("Both 'lat' and 'lng' must be provided together")
        return self


class ForecastQuery(WeatherQuery):
    anchor_date: date | None = None


class WeatherReading(BaseModel):
    weather: WeatherCondition
    temperature: float
    unit: TemperatureUnit


class CurrentWeatherResponse(WeatherReading):
    location: Coordinates
    resolved_city: str | None = None
    stale: bool = False


class DailyForecast(BaseModel):
    date: date
    weather: WeatherCondition
    temperature: float
    unit: TemperatureUnit


class ForecastResponse(BaseModel):
    location: Coordinates
    resolved_city: str | None = None
    days: list[DailyForecast]
    stale: bool = False
