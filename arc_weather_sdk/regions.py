from dataclasses import dataclass

from .models import Point


@dataclass(frozen=True, slots=True)
class Region:
    point: Point
    bounds: tuple[float, float, float, float]
    airports: tuple[str, ...]
    archive_stations: tuple[str, ...] = ()
    alert_areas: tuple[str, ...] = ()


REGIONS = {
    "moscow": Region(
        Point(55.7558, 37.6176), (37.1, 55.1, 37.97, 56.04),
        ("UUEE", "UUWW", "UUDD"), ("RSI0000UUDD", "RSMU0010909"), ("москва", "москвы"),
    ),
    "moscow-oblast": Region(
        Point(55.9167, 38), (35.1, 54.2, 40.3, 57),
        ("UUEE", "UUWW", "UUDD", "UUBW"), ("RSI0000UUDD",),
        ("москва", "москвы", "московская", "московской", "подмосков"),
    ),
    "sochi-adler": Region(
        Point(43.427, 39.923), (39.1, 43.2, 40.4, 44.1), ("URSS",), ("RSM00037171",),
        ("краснодарский", "краснодарского", "сочи", "адлер"),
    ),
    "primorye": Region(
        Point(43.1155, 131.8855), (130.4, 42.2, 139.1, 48.5), ("UHWW",), ("RSI0000UHWW", "RSM00031960"),
        ("приморский", "приморского", "владивосток"),
    ),
}
