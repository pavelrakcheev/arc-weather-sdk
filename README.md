# Arc Weather SDK

[![CI](https://github.com/pavelrakcheev/arc-weather-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/pavelrakcheev/arc-weather-sdk/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)

Arc Weather SDK — клиентская библиотека для [Arc Weather API](https://github.com/pavelrakcheev/arc-weather).
Она даёт приложению типизированный доступ к прогнозам, наблюдениям, архивам и планетарным данным,
не раскрывая ни источников, ни алгоритмов расчёта.

Модуль остаётся открытым: вы ставите пакет, создаёте `ArcWeatherClient` и получаете данные.
Ключи поставщиков, адреса источников и модели коррекции живут на стороне сервиса.

## Установка

Нужен Python 3.12 или новее.

```bash
python -m pip install "arc-weather-sdk @ git+https://github.com/pavelrakcheev/arc-weather-sdk.git@1.0.0"
```

Из рабочей копии пакет ставится командой `python -m pip install .`.

## Быстрый старт

```python
import httpx

from arc_weather_sdk import ArcWeatherClient, Point, format_weather

async def main():
    async with httpx.AsyncClient(timeout=15) as http:
        client = ArcWeatherClient(http, api_key="ak_...")
        result = await client.city("Владивосток", days=2)
        for item in result.items:
            print(format_weather(item))
```

Долгоживущему приложению стоит создать `httpx.AsyncClient` и `ArcWeatherClient` один раз при старте.
Клиент не владеет соединением — он использует ваш общий пул.

## Операции

| Метод | Что возвращает |
| --- | --- |
| `await client.forecast(Point(42.9, 131.65), days=10, hours=48)` | Прогноз по точке, отдельный результат каждого источника |
| `await client.city("Владивосток", days=2)` | Городская сводка с резервным выбором источника |
| `await client.place(Point(43.1155, 131.8855))` | Название места по координатам |
| `await client.search("Сочи")` | Список населённых пунктов по названию |
| `await client.radar()` | Манифест тайлов радара осадков |
| `await client.region("primorye")` | Наблюдения, предупреждения и архивы по региону |
| `await client.region("primorye", module="marine", operation="marine-stations")` | Та же область, но другая операция |
| `await client.planet("titan", limit=3000)` | Архив планетарной миссии |
| `await client.query("sinoptic", "city-forecast", CityQuery("Владивосток"))` | Любая операция каталога по имени |
| `await client.modules()` | Каталог модулей и операций |

Каждая операция возвращает `Result` с полями `module`, `operation`, `status` и `items`.

- Статусы `ok`, `empty`, `partial` и `unavailable` различают полученные данные, пустую выборку,
  частичный результат и недоступность всех источников.
- Элементы — это `Forecast`, `SourceData`, `PlanetaryData`, `SourceUnavailable` или словарь.
- `Forecast.current` — текущие условия: температура, ощущается, влажность, ветер с направлением
  и порывами, давление, облачность, осадки, ветер и порывы.
- `Forecast.daily` — суточный ряд: минимум, максимум, вероятность и сумма осадков, УФ-индекс,
  ветер, восход и закат, долгота дня.
- `Forecast.hourly` — почасовой ряд на 48 часов по умолчанию.
- `valid_at` — момент, на который рассчитано значение. `fetched_at` — время последней загрузки.
- `stale` отмечает сохранённый результат, выданный при сбое обновления.
- `source_url` и `license_url` позволяют указать атрибуцию в интерфейсе.
- В прогнозе температура в °C, ветер в км/ч, давление на уровне моря в гПа, влажность и
  вероятность осадков в процентах. Высота волн в метрах, период в секундах, направление в градусах.
- `current["condition"]` содержит описание погоды по-русски. Функция `condition(code)` переводит
  код WMO в текст, если вы работаете с сырыми кодами.
- `moon_phase(moment)` возвращает фазу Луны и освещённость доли диска.
- Значение `None` означает пропуск данных. Число `0` является полноценным измеряемым значением.

## Аутентификация и квоты

API работает по ключу, который передаётся в заголовке `X-API-Key`.

```python
client = ArcWeatherClient(http, api_key="ak_...")
```

Ключ задаётся один раз при создании клиента. Ответы содержат заголовки `X-RateLimit-Limit`,
`X-RateLimit-Remaining` и `X-RateLimit-Reset`. При превышении квоты API отвечает `429` с
`Retry-After`, а клиент выбрасывает `RateLimitError` с полем `retry_after`.

План подписки определяет лимиты запросов в минуту и в сутки. Ключи выдаются подрядчикам —
[условия и тарифы](https://github.com/pavelrakcheev/arc-weather).

## CLI

```bash
arc-weather --city Владивосток --days 3
arc-weather --point 42.9 131.65 --json
arc-weather --region sochi-adler --json
arc-weather --planet titan --limit 3 --json
arc-weather --list-modules
```

Адрес API и ключ берутся из `--api-url` и `--api-key` либо из переменных окружения
`ARC_WEATHER_API_URL` и `ARC_WEATHER_API_KEY`.

## Обработка ошибок

```python
from arc_weather_sdk import ApiError, AuthenticationError, RateLimitError

try:
    result = await client.city("Владивосток")
except AuthenticationError:
    ...  # ключ не задан или не действует
except RateLimitError as error:
    ...  # подождать error.retry_after секунд
except ApiError as error:
    ...  # error.status_code и error.detail
```

## Документация

- [Справочник API](docs/api.md) — эндпоинты, формат ответа и коды ошибок
- [Архитектура SDK](docs/architecture.md)

## Лицензия

MIT. См. файл [LICENSE](LICENSE). История изменений — в [CHANGELOG.md](CHANGELOG.md).
