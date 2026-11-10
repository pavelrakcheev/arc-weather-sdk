"""The uniform envelope returned by every Arc Weather API operation."""

from dataclasses import asdict, dataclass
from typing import Any, Literal

from .models import Forecast, PlanetaryData, SourceData, SourceUnavailable

Status = Literal["ok", "empty", "partial", "unavailable"]

Item = Forecast | SourceData | PlanetaryData | SourceUnavailable | dict[str, Any]


def item_type(item: Item) -> str:
    if isinstance(item, SourceUnavailable):
        return "unavailable"
    if isinstance(item, (Forecast, dict)):
        return "forecast"
    if isinstance(item, PlanetaryData):
        return "planetary-data"
    return "source-data"


def _status(items: tuple[Item, ...]) -> Status:
    failed = sum(isinstance(item, SourceUnavailable) for item in items)
    if failed:
        return "unavailable" if failed == len(items) else "partial"
    if any(not isinstance(item, (SourceData, PlanetaryData)) or item.records for item in items):
        return "ok"
    return "empty"


@dataclass(frozen=True, slots=True)
class Result:
    module: str
    operation: str
    status: Status
    items: tuple[Item, ...]

    def to_dict(self) -> dict:
        return {
            "module": self.module,
            "operation": self.operation,
            "status": self.status,
            "items": [
                {
                    **(item if isinstance(item, dict) else asdict(item)),
                    "type": item_type(item),
                }
                for item in self.items
            ],
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "Result":
        items = tuple(_item(raw) for raw in payload.get("items", []))
        return cls(
            module=payload["module"],
            operation=payload["operation"],
            status=payload.get("status") or _status(items),
            items=items,
        )


def _item(raw: dict) -> Item:
    data = {key: value for key, value in raw.items() if key != "type"}
    kind = raw.get("type")
    try:
        if kind == "forecast":
            return Forecast(**data)
        if kind == "unavailable":
            return SourceUnavailable(**data)
        if kind == "source-data":
            return SourceData(**data)
        if kind == "planetary-data":
            return PlanetaryData(**data)
    except TypeError:
        return data
    return data
