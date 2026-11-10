import unittest

import httpx

from arc_weather_sdk import (
    ArcWeatherClient, CityQuery, Forecast, NotFoundError, Point, RateLimitError,
    RegionalQuery, Result, SourceUnavailable, AuthenticationError, ApiError,
)

FORECAST_ITEM = {
    "type": "forecast",
    "module": "sinoptic",
    "source": "Open-Meteo",
    "valid_at": "2026-11-10T10:00:00+10:00",
    "fetched_at": "2026-11-10T09:58:11+10:00",
    "timezone": "Asia/Vladivostok",
    "current": {"temperature": 4.2, "weather_code": 3},
    "daily": [{"date": "2026-11-10", "min": 1.1, "max": 6.4}],
    "source_url": "https://open-meteo.com/",
    "license_url": "https://open-meteo.com/en/terms",
    "stale": False,
}

CITY_ITEM = {
    "type": "forecast",
    "city": "Владивосток",
    "country": "Россия",
    "timezone": "Asia/Vladivostok",
    "current": {"temperature": 4.2, "weather_code": 3, "condition": "облачно"},
    "daily": [{"date": "2026-11-10", "min": 1.1, "max": 6.4, "precipitation": 20}],
    "source": "Open-Meteo",
    "source_url": "https://open-meteo.com/",
    "license_url": "https://open-meteo.com/en/terms",
    "valid_at": "2026-11-10T10:00:00+10:00",
    "fetched_at": "2026-11-10T09:58:11+10:00",
    "stale": False,
}


def envelope(*items, status="ok", module="sinoptic", operation="forecast"):
    return {"module": module, "operation": operation, "status": status, "items": list(items)}


class ClientTests(unittest.IsolatedAsyncioTestCase):
    def client(self, handler, **kwargs):
        transport = httpx.MockTransport(handler)
        http = httpx.AsyncClient(transport=transport)
        self.addAsyncCleanup(http.aclose)
        return ArcWeatherClient(http, base_url="https://api.test", api_key="ak_test", **kwargs)

    async def test_forecast_sends_coordinates_and_returns_typed_items(self):
        seen = {}

        def handler(request):
            seen["params"] = dict(request.url.params)
            seen["key"] = request.headers.get("X-API-Key")
            return httpx.Response(200, json=envelope(FORECAST_ITEM))

        result = await self.client(handler).forecast(Point(42.9, 131.65), days=2)
        self.assertEqual(seen["params"], {"lat": "42.9", "lon": "131.65", "days": "2"})
        self.assertEqual(seen["key"], "ak_test")
        self.assertEqual(result.status, "ok")
        self.assertIsInstance(result.items[0], Forecast)
        self.assertEqual(result.items[0].source, "Open-Meteo")

    async def test_city_returns_the_summary_payload(self):
        def handler(request):
            return httpx.Response(200, json=envelope(CITY_ITEM, operation="city-forecast"))

        payload = await self.client(handler).fetch_weather("Владивосток", days=2)
        self.assertEqual(payload["city"], "Владивосток")
        self.assertEqual(payload["current"]["condition"], "облачно")

    async def test_partial_result_keeps_the_unavailable_source(self):
        def handler(request):
            return httpx.Response(200, json=envelope(
                FORECAST_ITEM,
                {"type": "unavailable", "module": "sinoptic", "source": "MET Norway"},
                status="partial",
            ))

        result = await self.client(handler).forecast(Point(43, 131))
        self.assertEqual(result.status, "partial")
        self.assertIsInstance(result.items[1], SourceUnavailable)
        self.assertEqual(result.items[1].source, "MET Norway")

    async def test_region_accepts_a_preset_and_a_custom_area(self):
        seen = []

        def handler(request):
            seen.append(dict(request.url.params))
            return httpx.Response(200, json=envelope(status="ok", operation="metar"))

        client = self.client(handler)
        await client.region("primorye")
        await client.region("primorye", point=Point(43, 131))
        await client.region("primorye", module="marine", operation="marine-stations")
        self.assertEqual(seen[0]["preset"], "primorye")
        self.assertEqual(seen[0]["operation"], "metar")
        self.assertEqual(seen[1]["lat"], "43.0")
        self.assertEqual(seen[2]["module"], "marine")

    async def test_unknown_preset_is_rejected_before_the_request(self):
        def handler(request):
            raise AssertionError("the client must not call the API")

        with self.assertRaises(ValueError):
            await self.client(handler).region("atlantis")

    async def test_query_encodes_the_request_type(self):
        seen = {}

        def handler(request):
            seen["body"] = request.read().decode()
            return httpx.Response(200, json=envelope(CITY_ITEM, operation="city-forecast"))

        await self.client(handler).query("sinoptic", "city-forecast", CityQuery("Владивосток"))
        self.assertIn('"city":"Владивосток"', seen["body"])

    async def test_modules_returns_the_catalogue(self):
        def handler(request):
            return httpx.Response(200, json=[{"id": "sinoptic", "name": "Arc Sinoptic"}])

        catalogue = await self.client(handler).modules()
        self.assertEqual(catalogue[0]["id"], "sinoptic")

    async def test_missing_key_raises_an_authentication_error(self):
        def handler(request):
            return httpx.Response(401, json={"detail": "unknown key"})

        with self.assertRaises(AuthenticationError):
            await self.client(handler).city("Владивосток")

    async def test_rate_limit_carries_the_retry_after_header(self):
        def handler(request):
            return httpx.Response(429, json={"detail": "quota"}, headers={"Retry-After": "42"})

        with self.assertRaises(RateLimitError) as error:
            await self.client(handler).city("Владивосток")
        self.assertEqual(error.exception.retry_after, 42)

    async def test_missing_resource_raises_a_not_found_error(self):
        def handler(request):
            return httpx.Response(404, json={"detail": "no such planet"})

        with self.assertRaises(NotFoundError):
            await self.client(handler).planet("pluto")

    async def test_unreachable_service_raises_an_api_error(self):
        def handler(request):
            raise httpx.ConnectError("boom", request=request)

        with self.assertRaises(ApiError):
            await self.client(handler).city("Владивосток")


class ResultTests(unittest.TestCase):
    def test_from_dict_restores_typed_items(self):
        result = Result.from_dict(envelope(FORECAST_ITEM))
        self.assertEqual(result.module, "sinoptic")
        self.assertIsInstance(result.items[0], Forecast)

    def test_to_dict_round_trips(self):
        result = Result.from_dict(envelope(FORECAST_ITEM))
        again = Result.from_dict(result.to_dict())
        self.assertEqual(again.items[0], result.items[0])

    def test_unknown_item_types_stay_plain_dictionaries(self):
        result = Result.from_dict(envelope({"type": "mystery", "value": 1}))
        self.assertEqual(result.items[0], {"value": 1})
