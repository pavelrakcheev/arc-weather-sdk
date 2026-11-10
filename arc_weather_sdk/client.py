"""HTTP client for the Arc Weather API."""

from datetime import date
from typing import Any

import httpx

from ._version import __version__
from .errors import ApiError, AuthenticationError, NotFoundError, RateLimitError
from .models import Point
from .queries import CityQuery, ForecastQuery, PlanetQuery, RegionalQuery
from .regions import REGIONS, Region
from .result import Result

DEFAULT_BASE_URL = "https://api.arcweather.dev"
DEFAULT_TIMEOUT = 15.0


class ArcWeatherClient:
    """Talk to the Arc Weather API.

    The client never owns the HTTP connection: pass the ``httpx.AsyncClient``
    that the host application already uses, so every call shares its pool.
    """

    def __init__(
        self,
        http: httpx.AsyncClient,
        *,
        base_url: str = DEFAULT_BASE_URL,
        api_key: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        self._http = http
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._user_agent = user_agent or f"arc-weather-sdk/{__version__}"

    @property
    def base_url(self) -> str:
        return self._base_url

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json", "User-Agent": self._user_agent}
        if self._api_key:
            headers["X-API-Key"] = self._api_key
        return headers

    async def _request(self, method: str, path: str, **kwargs: Any) -> Result:
        url = f"{self._base_url}{path}"
        try:
            response = await self._http.request(
                method, url, headers=self._headers(), timeout=kwargs.pop("timeout", DEFAULT_TIMEOUT), **kwargs
            )
        except httpx.HTTPError as error:
            raise ApiError(f"Arc Weather API is unreachable: {error}") from error
        if response.status_code >= 400:
            raise self._error(response)
        return Result.from_dict(response.json())

    @staticmethod
    def _error(response: httpx.Response) -> ApiError:
        detail: Any = response.text
        try:
            payload = response.json()
            detail = payload.get("detail", payload)
        except ValueError:
            pass
        message = f"Arc Weather API returned {response.status_code}"
        if response.status_code in (401, 403):
            return AuthenticationError(f"{message}: {detail}")
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After") or 0)
            return RateLimitError(f"{message}: {detail}", retry_after=retry_after)
        if response.status_code == 404:
            return NotFoundError(f"{message}: {detail}", status_code=404, detail=detail)
        return ApiError(f"{message}: {detail}", status_code=response.status_code, detail=detail)

    async def forecast(self, point: Point, *, days: int = 1) -> Result:
        """Point forecast for every provider that covers the location."""
        return await self._request(
            "GET", "/v1/forecast",
            params={"lat": point.latitude, "lon": point.longitude, "days": days},
        )

    async def city(self, name: str, *, days: int = 1) -> Result:
        """City forecast with the provider fallback already applied."""
        return await self._request("GET", "/v1/city", params={"name": name, "days": days})

    async def region(
        self,
        region: str | Region,
        *,
        point: Point | None = None,
        archive_day: date | None = None,
    ) -> Result:
        """Observations, alerts and archives for a named preset or a custom area."""
        params: dict[str, Any] = {}
        if isinstance(region, Region):
            params.update({
                "lat": region.point.latitude, "lon": region.point.longitude,
                "west": region.bounds[0], "south": region.bounds[1],
                "east": region.bounds[2], "north": region.bounds[3],
            })
            if region.airports:
                params["airports"] = ",".join(region.airports)
            if region.archive_stations:
                params["stations"] = ",".join(region.archive_stations)
            if region.alert_areas:
                params["areas"] = ",".join(region.alert_areas)
        else:
            if region not in REGIONS:
                raise ValueError(f"Unknown region: {region}")
            params["preset"] = region
        if point is not None:
            params.update({"lat": point.latitude, "lon": point.longitude})
        if archive_day is not None:
            params["archive_day"] = archive_day.isoformat()
        return await self._request("GET", "/v1/region", params=params)

    async def planet(self, planet: str, *, sol: int | None = None, limit: int = 100) -> Result:
        """Archive of a planetary mission."""
        params: dict[str, Any] = {"planet": planet, "limit": limit}
        if sol is not None:
            params["sol"] = sol
        return await self._request("GET", "/v1/planet", params=params)

    async def query(self, module: str, operation: str, request: Any) -> Result:
        """Call any operation of the API catalogue by name."""
        payload = {"module": module, "operation": operation, "request": _encode_request(request)}
        return await self._request("POST", "/v1/query", json=payload)

    async def modules(self) -> list[dict]:
        """Catalogue of the modules and operations the API exposes."""
        url = f"{self._base_url}/v1/modules"
        response = await self._http.get(url, headers=self._headers(), timeout=DEFAULT_TIMEOUT)
        if response.status_code >= 400:
            raise self._error(response)
        return response.json()

    async def fetch_weather(self, city: str, *, days: int = 1) -> dict:
        """City forecast as a plain dict, ready for :func:`format_weather`."""
        result = await self.city(city, days=days)
        payload = result.items[0] if result.items else None
        if payload is None or not isinstance(payload, dict):
            raise ApiError("Arc Weather API returned no forecast for this city")
        return payload


def _encode_request(request: Any) -> dict:
    if isinstance(request, ForecastQuery):
        return {"point": {"latitude": request.point.latitude, "longitude": request.point.longitude},
                "days": request.days}
    if isinstance(request, CityQuery):
        return {"city": request.city, "days": request.days}
    if isinstance(request, RegionalQuery):
        return {
            "region": {
                "point": {"latitude": request.region.point.latitude,
                          "longitude": request.region.point.longitude},
                "bounds": list(request.region.bounds),
                "airports": list(request.region.airports),
                "archive_stations": list(request.region.archive_stations),
                "alert_areas": list(request.region.alert_areas),
            },
            "point": None if request.point is None else {
                "latitude": request.point.latitude, "longitude": request.point.longitude},
            "archive_day": request.archive_day.isoformat() if request.archive_day else None,
        }
    if isinstance(request, PlanetQuery):
        return {"sol": request.sol, "limit": request.limit}
    if isinstance(request, dict):
        return request
    raise TypeError(f"Unsupported request type: {type(request).__name__}")
