import contextlib
import io
import json
import unittest
from unittest import mock

from arc_weather_sdk import Result, __version__
from arc_weather_sdk.__main__ import main


class FakeClient:
    def __init__(self, *args, **kwargs):
        self.calls = []

    async def modules(self):
        return [{"id": "sinoptic", "name": "Arc Sinoptic"}]

    async def city(self, name, *, days=1):
        self.calls.append(("city", name, days))
        return Result("sinoptic", "city-forecast", "ok", ({
            "city": name, "country": "Россия", "timezone": "Asia/Vladivostok",
            "current": {"temperature": 4.2, "condition": "облачно"},
            "daily": [], "source": "Open-Meteo",
            "source_url": "https://open-meteo.com/", "license_url": "https://open-meteo.com/en/terms",
            "valid_at": "2026-11-10T10:00:00+10:00", "fetched_at": "2026-11-10T09:58:11+10:00",
            "stale": False,
        },))

    async def forecast(self, point, *, days=1):
        self.calls.append(("forecast", point, days))
        return Result("sinoptic", "forecast", "ok", ())

    async def planet(self, planet, *, sol=None, limit=100):
        self.calls.append(("planet", planet, sol, limit))
        return Result("mars", "archive", "empty", ())


class CliTests(unittest.TestCase):
    def run_cli(self, *argv):
        buffer = io.StringIO()
        with mock.patch("arc_weather_sdk.__main__.ArcWeatherClient", FakeClient):
            with mock.patch("sys.argv", ["arc-weather", *argv]):
                with contextlib.redirect_stdout(buffer):
                    code = main()
        return code, buffer.getvalue()

    def test_version_prints_the_package_version(self):
        code, output = self.run_cli("--version")
        self.assertEqual(code, 0)
        self.assertEqual(output.strip(), f"arc-weather-sdk {__version__}")

    def test_list_modules_prints_the_catalogue(self):
        code, output = self.run_cli("--list-modules")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output)[0]["id"], "sinoptic")

    def test_city_renders_the_text_card(self):
        code, output = self.run_cli("--city", "Владивосток", "--days", "2")
        self.assertEqual(code, 0)
        self.assertIn("Погода · Владивосток, Россия", output)
        self.assertIn("Open-Meteo", output)

    def test_city_can_return_json(self):
        code, output = self.run_cli("--city", "Владивосток", "--json")
        self.assertEqual(code, 0)
        payload = json.loads(output)
        self.assertEqual(payload["operation"], "city-forecast")

    def test_a_location_argument_is_required(self):
        with mock.patch("sys.argv", ["arc-weather"]):
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    main()
        self.assertNotEqual(error.exception.code, 0)
