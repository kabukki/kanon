from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    fictional_weather_api_base_url: str = "https://api.fictionalweather.example.com"
    fictional_weather_api_key: str = ""

    mapbox_base_url: str = "https://api.mapbox.com"
    mapbox_token: str = ""

    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_current_seconds: int = 600
    cache_ttl_forecast_seconds: int = 3600
    cache_ttl_geocode_seconds: int = 86400 * 30

    sentry_dsn: str = ""
    environment: str = "development"

    rate_limit_per_minute: int = 60

    http_timeout_seconds: float = 3.0


settings = Settings()
