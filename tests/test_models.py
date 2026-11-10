import unittest
from datetime import datetime, timezone

from arc_weather_sdk import Point, Region, REGIONS, format_weather, moon_phase, weather_payload, Forecast


class ModelTests(unittest.TestCase):
    def test_point_rounds_to_four_decimals(self):
        self.assertEqual(Point(43.123456, 131.654321).latitude, 43.1235)
        self.assertEqual(Point(43.123456, 131.654321).longitude, 131.6543)

    def test_point_rejects_out_of_range_values(self):
        with self.assertRaises(ValueError):
            Point(91, 0)
        with self.assertRaises(ValueError):
            Point(0, 181)

    def test_region_presets_are_complete(self):
        self.assertEqual(set(REGIONS), {"moscow", "moscow-oblast", "sochi-adler", "primorye"})
        for name, region in REGIONS.items():
            self.assertIsInstance(region, Region)
            self.assertEqual(len(region.bounds), 4)
            self.assertTrue(region.airports, name)

    def test_weather_payload_keeps_provenance(self):
        forecast = Forecast(
            module="sinoptic", source="Open-Meteo",
            valid_at="2026-11-10T10:00:00+10:00", fetched_at="2026-11-10T09:58:11+10:00",
            timezone="Asia/Vladivostok", current={"temperature": 4.2, "weather_code": 3},
            source_url="https://open-meteo.com/", license_url="https://open-meteo.com/en/terms",
            daily=({"date": "2026-11-10", "min": 1.1, "max": 6.4},),
        )
        payload = weather_payload("Владивосток", "Россия", forecast)
        self.assertEqual(payload["city"], "Владивосток")
        self.assertEqual(payload["current"]["condition"], "облачно")
        self.assertEqual(payload["source"], "Open-Meteo")

    def test_the_weather_code_survives_the_condition(self):
        forecast = Forecast(
            module="sinoptic", source="Open-Meteo",
            valid_at="2026-11-10T10:00:00+10:00", fetched_at="2026-11-10T09:58:11+10:00",
            timezone="UTC", current={"temperature": 4.2, "weather_code": 61},
            source_url="https://open-meteo.com/", license_url="https://open-meteo.com/en/terms",
        )
        payload = weather_payload("Точка", "", forecast)
        self.assertEqual(payload["current"]["weather_code"], 61)
        self.assertEqual(payload["current"]["condition"], "слабый дождь")

    def test_format_weather_renders_a_russian_card(self):
        forecast = Forecast(
            module="sinoptic", source="Open-Meteo",
            valid_at="2026-11-10T10:00:00+10:00", fetched_at="2026-11-10T09:58:11+10:00",
            timezone="Asia/Vladivostok", current={"temperature": 4.2, "weather_code": 3},
            source_url="https://open-meteo.com/", license_url="https://open-meteo.com/en/terms",
            daily=({"date": "2026-11-10", "min": 1.1, "max": 6.4},),
        )
        card = format_weather(weather_payload("Владивосток", "Россия", forecast))
        self.assertIn("Владивосток", card)
        self.assertIn("Температура · 4.2 °C", card)
        self.assertIn("Open-Meteo", card)

    def test_missing_values_are_skipped_and_zero_is_kept(self):
        forecast = Forecast(
            module="sinoptic", source="Open-Meteo",
            valid_at="2026-11-10T10:00:00+10:00", fetched_at="2026-11-10T09:58:11+10:00",
            timezone="UTC", current={"temperature": 0, "humidity": None, "weather_code": 0},
            source_url="https://open-meteo.com/", license_url="https://open-meteo.com/en/terms",
        )
        card = format_weather(weather_payload("Точка", "", forecast))
        self.assertIn("Температура · 0 °C", card)
        self.assertNotIn("Влажность", card)


class MoonTests(unittest.TestCase):
    def test_a_new_moon_has_no_illumination(self):
        phase = moon_phase(datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc))
        self.assertEqual(phase["phase"], "Новолуние")
        self.assertLess(phase["illumination"], 5)

    def test_a_full_moon_is_fully_illuminated(self):
        phase = moon_phase(datetime(2023, 1, 6, 18, 24, tzinfo=timezone.utc))
        self.assertEqual(phase["phase"], "Полнолуние")
        self.assertGreater(phase["illumination"], 95)

    def test_the_age_stays_inside_the_synodic_month(self):
        for day in range(1, 29):
            phase = moon_phase(datetime(2026, 11, day, 12, tzinfo=timezone.utc))
            self.assertGreaterEqual(phase["age"], 0)
            self.assertLess(phase["age"], 29.6)
