from .models import Forecast

_CONDITIONS = {
    0: "ясно", 1: "преимущественно ясно", 2: "переменная облачность", 3: "облачно",
    45: "туман", 48: "туман с изморозью", 51: "слабая морось", 53: "морось",
    55: "сильная морось", 56: "ледяная морось", 57: "сильная ледяная морось",
    61: "слабый дождь", 63: "дождь", 65: "сильный дождь", 66: "ледяный дождь",
    67: "сильный ледяный дождь", 71: "слабый снег", 73: "снег", 75: "сильный снег",
    77: "снежные зёрна", 80: "ливневый дождь", 81: "ливень", 82: "сильный ливень",
    85: "снежный заряд", 86: "сильный снежный заряд", 95: "гроза",
    96: "гроза с градом", 99: "сильная гроза с градом",
}


def _with_condition(data: dict) -> dict:
    values = dict(data)
    code = values.pop("weather_code", None)
    values["condition"] = values.get("condition") or _CONDITIONS.get(code, "неизвестно")
    return values


def weather_payload(name: str, country: str, result: Forecast) -> dict:
    """Build a plain, JSON-serialisable city forecast with provenance."""
    return {
        "city": name,
        "country": country,
        "timezone": result.timezone,
        "current": _with_condition(result.current),
        "daily": [_with_condition(day) for day in result.daily],
        "source": result.source,
        "source_url": result.source_url,
        "license_url": result.license_url,
        "valid_at": result.valid_at,
        "fetched_at": result.fetched_at,
        "stale": result.stale,
    }


def format_weather(data: dict) -> str:
    """Render a short Russian plain-text card from a weather payload."""
    place = ", ".join(filter(None, (data["city"], data["country"])))
    current = data["current"]
    lines = [f"Погода · {place}"]
    if data["stale"]:
        lines.append("Последние сохранённые данные")
    for key, label, unit in (
        ("temperature", "Температура", "°C"),
        ("apparent", "Ощущается как", "°C"),
        ("humidity", "Влажность", "%"),
        ("wind", "Ветер", "км/ч"),
        ("pressure_msl_hpa", "Давление на уровне моря", "гПа"),
        ("pressure_hpa", "Давление", "гПа"),
    ):
        if current.get(key) is not None:
            lines.append(f"{label} · {current[key]:g} {unit}")

    if current["condition"] != "неизвестно":
        lines.append(current["condition"].capitalize())

    for day in data["daily"]:
        low = f'{day["min"]:g} °C' if day.get("min") is not None else "—"
        high = f'{day["max"]:g} °C' if day.get("max") is not None else "—"
        rain = f' · осадки до {day["precipitation"]:g}%' if day.get("precipitation") is not None else ""
        if day.get("rain_probability_pct") is not None:
            rain += f' · дождь {day["rain_probability_pct"]:g}%'
        if day.get("snow_probability_pct") is not None:
            rain += f' · снег {day["snow_probability_pct"]:g}%'
        lines.append(f'{day["date"]} · мин. {low} · макс. {high}{rain}')

    lines.append(f'{data["source"]} · на {data["valid_at"].replace("T", " ")}')
    lines.append(f'{data["source_url"]} · {data["license_url"]} · данные адаптированы')
    return "\n".join(lines)
