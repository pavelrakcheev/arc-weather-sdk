# Changelog

Все значимые изменения проекта отмечаются в этом файле. Формат основан на
[Keep a Changelog](https://keepachangelog.com/ru/1.1.0/), версионирование — по
[SemVer](https://semver.org/lang/ru/).

## [1.0.0] — 2026-11-10

Первый публичный релиз клиентской библиотеки.

### Добавлено

- `ArcWeatherClient` — асинхронный клиент Arc Weather API с общим `httpx.AsyncClient`
  приложения.
- Операции `forecast`, `city`, `region`, `planet`, `query` и `modules`.
- Модели `Point`, `Forecast`, `SourceData`, `PlanetaryData` и `SourceUnavailable`.
- Конверт `Result` со статусами `ok`, `empty`, `partial` и `unavailable`.
- Типы запросов `ForecastQuery`, `CityQuery`, `RegionalQuery` и `PlanetQuery`.
- Профили регионов `REGIONS` с Москвой, Подмосковьем, Сочи–Адлером и Приморьем.
- `weather_payload` и `format_weather` для текстовой карточки прогноза на русском.
- Исключения `ArcWeatherError`, `AuthenticationError`, `RateLimitError`, `ApiError`
  и `NotFoundError`.
- CLI `arc-weather` с командами `--city`, `--point`, `--region`, `--planet`,
  `--operation`, `--list-modules` и `--version`.
- Маркер `py.typed` и публичные аннотации типов.
- CI на Python 3.12–3.14, лицензия MIT и журнал изменений.
