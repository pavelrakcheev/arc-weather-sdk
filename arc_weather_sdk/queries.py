"""Request types accepted by the Arc Weather API."""

from dataclasses import dataclass
from datetime import date

from .models import Point
from .regions import Region


@dataclass(frozen=True, slots=True)
class ForecastQuery:
    point: Point
    days: int = 1
    hours: int = 48


@dataclass(frozen=True, slots=True)
class PointQuery:
    """A request that only needs a position."""

    point: Point


@dataclass(frozen=True, slots=True)
class CityQuery:
    city: str
    days: int = 1


@dataclass(frozen=True, slots=True)
class RegionalQuery:
    region: Region
    point: Point | None = None
    archive_day: date | None = None


@dataclass(frozen=True, slots=True)
class PlanetQuery:
    sol: int | None = None
    limit: int = 100
