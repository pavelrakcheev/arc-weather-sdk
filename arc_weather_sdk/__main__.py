"""Command line interface for the Arc Weather API."""

import argparse
import asyncio
import json
import os
import sys

import httpx

from ._version import __version__
from .client import DEFAULT_BASE_URL, ArcWeatherClient
from .errors import ArcWeatherError
from .models import Point
from .queries import CityQuery, ForecastQuery, PlanetQuery, RegionalQuery
from .regions import REGIONS
from .result import Result


def _print_result(result: Result, as_json: bool) -> int:
    if as_json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return 0
    if result.status == "unavailable":
        print("Источники недоступны", file=sys.stderr)
        return 1
    for item in result.items:
        if isinstance(item, dict):
            print(json.dumps(item, ensure_ascii=False, indent=2))
        else:
            print(item)
    return 0


async def _run(args: argparse.Namespace) -> int:
    headers = {"User-Agent": f"arc-weather-sdk/{__version__}"}
    async with httpx.AsyncClient(timeout=args.timeout) as http:
        client = ArcWeatherClient(
            http, base_url=args.api_url, api_key=args.api_key, user_agent=headers["User-Agent"]
        )
        if args.list_modules:
            print(json.dumps(await client.modules(), ensure_ascii=False, indent=2))
            return 0
        if args.operation:
            module, operation = args.operation
            request = json.loads(args.request) if args.request else {}
            result = await client.query(module, operation, request)
            return _print_result(result, args.json)
        if args.city is not None:
            result = await client.city(args.city, days=args.days)
            if args.json:
                return _print_result(result, True)
            item = result.items[0] if result.items else None
            if not isinstance(item, dict):
                print("Источники недоступны", file=sys.stderr)
                return 1
            from .presentation import format_weather
            print(format_weather(item))
            return 0
        if args.point is not None:
            point = Point(*args.point)
            result = await client.forecast(point, days=args.days)
            return _print_result(result, args.json)
        if args.region is not None:
            result = await client.region(args.region)
            return _print_result(result, args.json)
        if args.planet is not None:
            result = await client.planet(args.planet, sol=args.sol, limit=args.limit or 100)
            return _print_result(result, args.json)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Arc Weather · клиент Arc Weather API")
    location = parser.add_mutually_exclusive_group(required=True)
    location.add_argument("--city")
    location.add_argument("--point", nargs=2, type=float, metavar=("LAT", "LON"))
    location.add_argument("--region", choices=sorted(REGIONS))
    location.add_argument("--planet", choices=("mars", "venus", "titan"))
    location.add_argument("--operation", nargs=2, metavar=("MODULE", "OPERATION"))
    location.add_argument("--list-modules", action="store_true", help="каталог модулей и операций")
    location.add_argument("--version", action="store_true", help="показать версию и выйти")
    parser.add_argument("--request", help="JSON-тело запроса для --operation")
    parser.add_argument("--days", type=int, choices=range(1, 4), default=1)
    parser.add_argument("--sol", type=int)
    parser.add_argument("--limit", type=int, metavar="ROWS")
    parser.add_argument("--json", action="store_true", help="вывод JSON")
    parser.add_argument("--api-url", default=os.getenv("ARC_WEATHER_API_URL", DEFAULT_BASE_URL))
    parser.add_argument("--api-key", default=os.getenv("ARC_WEATHER_API_KEY"))
    parser.add_argument("--timeout", type=float, default=15.0)
    args = parser.parse_args()
    if args.version:
        print(f"arc-weather-sdk {__version__}")
        return 0
    try:
        return asyncio.run(_run(args))
    except ArcWeatherError as error:
        parser.exit(1, f"Arc Weather: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
