class WeatherAPIError(Exception):
    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code


class BadRequestError(WeatherAPIError):
    status_code = 400
    code = "bad_request"


class NotFoundError(WeatherAPIError):
    status_code = 404
    code = "not_found"


class UpstreamUnavailableError(WeatherAPIError):
    status_code = 503
    code = "upstream_unavailable"


class InternalServerError(WeatherAPIError):
    status_code = 500
    code = "internal_error"
