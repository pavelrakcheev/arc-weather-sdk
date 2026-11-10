from dataclasses import dataclass
from math import isfinite
from typing import Any


@dataclass(frozen=True, slots=True)
class Point:
    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        for name, value, limit in (
            ("latitude", self.latitude, 90),
            ("longitude", self.longitude, 180),
        ):
            if not isfinite(value) or not -limit <= value <= limit:
                raise ValueError(f"{name} must be between {-limit} and {limit}")
            object.__setattr__(self, name, round(float(value), 4) or 0.0)


@dataclass(frozen=True, slots=True)
class Forecast:
    module: str
    source: str
    valid_at: str
    fetched_at: str
    timezone: str
    current: dict[str, Any]
    source_url: str
    license_url: str
    daily: tuple[dict[str, Any], ...] = ()
    hourly: tuple[dict[str, Any], ...] = ()
    stale: bool = False


@dataclass(frozen=True, slots=True)
class SourceUnavailable:
    module: str
    source: str


@dataclass(frozen=True, slots=True)
class SourceData:
    module: str
    source: str
    kind: str
    fetched_at: str
    records: list[dict[str, Any]]


@dataclass(frozen=True, slots=True)
class PlanetaryData:
    module: str
    body: str
    mission: str
    source: str
    kind: str
    fetched_at: str
    records: list[dict[str, Any]]
