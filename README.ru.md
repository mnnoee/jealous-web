# jealous-web

[README in English](README.md)

[![CI](https://github.com/mnnoee/jealous-web/actions/workflows/ci.yml/badge.svg)](https://github.com/mnnoee/jealous-web/actions/workflows/ci.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-0.1.0-green.svg)](CHANGELOG.md)

> Часть набора инструментов [Jealous Moon](https://github.com/mnnoee) —
> офлайн-диагностики серверов и доменов.

Проверка одной страницы и **всех её ресурсов**: тайминги в стиле `httpstat`
(DNS / TCP / TLS / TTFB / передача), размеры, версия HTTP, заголовки, редиректы
и перекрёстные проверки. Не краулер: открывает одну страницу и вытаскивает
только то, что реально упомянуто в HTML и CSS.

Самодостаточный CLI-инструмент: пакет чистых функций `webcheck/` + тонкая
обёртка `web_checker.py`. Загрузка — через `curl`, как `dig`/`openssl` в
остальных модулях набора: без зависимостей Python.

## Возможности

- **Секция страницы** (`--page`): статус, версия HTTP, content-type,
  переданный размер, удалённый IP:порт, цепочка редиректов, тайминги по фазам,
  заголовки (`server`, `content-encoding`, `cache-control`, HSTS).
- **Секция ресурсов** (`--assets`): `script`, `link` (stylesheet /
  modulepreload / preload с `as` / icon / manifest), `img` и `srcset`,
  `source`, `video`/`audio`/`track`/`embed`, `object`, `iframe`, `poster`,
  inline-`<style>` и `style=""`, `url()` и `@import` внутри CSS.
- **Волны CSS**: ссылки из CSS раскрываются рекурсивно (`--css-depth`, по
  умолчанию 3), внешние `@import` тоже находятся.
- **Реалистичный запрос**: `Accept-Encoding` (gzip/br), HTTP/2, свой
  User-Agent (`--user-agent`), опционально `--insecure`.
- **Размеры — переданные байты** (со сжатием), а не распакованный HTML:
  видно, сколько страница реально тянет по сети.
- **Кодировки**: charset берётся из заголовка или `<meta charset>`, поэтому
  страницы в windows-1251/koi8-r не дают битых ссылок.
- **Перекрёстные проверки** (эвристики): нет HSTS, ответ без сжатия,
  дублирующиеся заголовки, ресурсы 4xx/5xx, смешанный контент, сторонние
  хосты, тяжёлые ресурсы, медленный TTFB, HTTP/1.1, отсутствие `cache-control`.
- **Изоляция секций**: страница не загрузилась — `error` в секции, отчёт и
  JSON всё равно собираются.
- **IDN**: `смешнявки.рф` на сетевой границе превращается в punycode.
- **JSON-отчёт** (`--json [PATH]`) — `meta` + `page` + `assets` +
  `cross_checks`, как у остальных модулей набора.

> **Важно:** вывод — эвристика, а не приговор. Пороги (TTFB 600 мс, страница
> 2 МБ, ресурс 500 КБ, HSTS 180 дней) — повод проверить, а не вердикт.
> Каждый ресурс качается отдельным процессом `curl`, поэтому DNS/TCP/TLS
> показывают цену **нового** соединения, а не переиспользованного браузером.
> JS не исполняется: для SPA список ресурсов будет неполным. Тело страницы
> больше 5 МБ не разбирается (защита от гигантских ответов).

## Зависимости

- Python 3 (только стандартная библиотека).
- `curl` в PATH, собранный с HTTP/2 (нужен для `--http2` и таймингов).
  Проверка: `curl --version`.

## Установка

Пока не на PyPI (публикация планируется). Ставится напрямую с GitHub:

```bash
pip install git+https://github.com/mnnoee/jealous-web.git
```

После установки доступна команда `jealous-web`. Можно запускать и без
установки — прямо из клона репозитория:

```bash
python3 web_checker.py example.com
```

## Использование

```
jealous-web example.com                     # страница + все ресурсы
jealous-web example.com --page              # только страница
jealous-web example.com --assets            # только ресурсы
jealous-web example.com --filter css,js,font
jealous-web example.com --css-depth 1
jealous-web example.com --diagram           # httpstat-диаграммы
jealous-web example.com --json              # отчёт в report.json
jealous-web example.com --json out.json
jealous-web --version
```

Схему можно не указывать: без неё подставляется `https://`.

### Опции

| Флаг | Описание |
|------|----------|
| `--page` | секция страницы |
| `--assets` | секция ресурсов |
| `--all` | обе секции (поведение по умолчанию) |
| `-j`, `--workers N` | параллельных загрузок (по умолчанию 10) |
| `-t`, `--timeout SEC` | таймаут на запрос (по умолчанию 20) |
| `--css-depth N` | глубина раскрытия CSS (по умолчанию 3) |
| `--filter LIST` | типы ресурсов через запятую: `css,js,img,font,...` |
| `--top N` | сколько медленных ресурсов показывать (по умолчанию 10) |
| `--no-http2` | не просить HTTP/2 |
| `--no-compress` | не просить сжатие (`Accept-Encoding: identity`) |
| `--insecure` | не проверять TLS-сертификат |
| `--user-agent UA` | свой User-Agent |
| `--diagram` | httpstat-диаграммы по каждому запросу |
| `--json [PATH]` | машиночитаемый отчёт (по умолчанию `report.json`) |

Без флагов запускаются обе секции. Один флаг на секцию — это будущие чекбоксы
UI один-в-один, без промежуточного маппинга.

## Пример отчёта

```
==================================================
example.com
==================================================

--- Страница ---
  статус:      200
  HTTP:        2
  финальный:   https://example.com/
  тип:         text/html; charset=UTF-8
  размер:      12.1K (передано)
  удалённый:   203.0.113.10:443
  редиректы:   1 (301 https://example.com/)
  DNS:         7 ms
  TCP:         60 ms
  TLS:         65 ms
  TTFB:        250 ms
  передача:    30 ms
  всего:       395 ms
  server:      nginx
  encoding:    gzip
  cache:       max-age=600
  hsts:        max-age=31536000

--- Ресурсы (4) ---
STAT  TYPE         VER        DNS   TCP   TLS  TTFB  TOTAL     SIZE  URL
------------------------------------------------------------------------
 200  css          HTTP/2      18    61    64   190    330     3.3K  https://example.com/site.css
 200  js           HTTP/2      19    62    65   191    331     1.0K  https://example.com/app.js
 200  img          HTTP/2      17    60    63   188    328     5.5K  https://example.com/logo.png

--- По типам ---
  img          n=1   size=5.5K
  css          n=1   size=3.3K
  js           n=1   size=1.0K

--- Проверки ---
  [info] у статических ресурсов нет cache-control
  [info] нет заголовков безопасности: referrer-policy

* каждый ресурс качается отдельным процессом curl: DNS/TCP/TLS -
  цена нового соединения, а не переиспользованного браузером
* размер - переданные байты (со сжатием); это срез на момент проверки
```

## JSON-отчёт

```json
{
  "meta": {
    "version": "0.1.0",
    "url": "example.com",
    "final_url": "https://example.com/",
    "checked_at": "2026-10-29T12:00:00+00:00",
    "elapsed_sec": 1.31,
    "sections_run": ["page", "assets"],
    "status": 200,
    "http_version": "2",
    "bytes_page": 12112,
    "resources_total": 13,
    "resources_ok": 13,
    "resources_failed": 0,
    "bytes_total": 87000
  },
  "page": {
    "url": "https://example.com/",
    "final_url": "https://example.com/",
    "status": 200,
    "http_version": "2",
    "content_type": "text/html; charset=UTF-8",
    "size": 12112,
    "timings_ms": {"dns": 7, "tcp": 60, "tls": 65,
                   "redirect": 0, "ttfb": 250,
                   "transfer": 30, "total": 395},
    "redirects": [{"status": 301, "location": "https://example.com/"}],
    "headers": {"server": ["nginx"], "cache-control": ["max-age=600"]},
    "error": null
  },
  "assets": {
    "items": [
      {"url": "https://example.com/site.css", "final_url": "https://example.com/site.css",
       "type": "css", "status": 200, "http_version": "2",
       "content_type": "text/css", "size": 3379,
       "timings_ms": {"dns": 18, "tcp": 61, "tls": 64,
                      "redirect": 0, "ttfb": 190,
                      "transfer": 0, "total": 330},
       "redirects": [], "headers": {}, "error": null}
    ],
    "by_type": [{"type": "css", "count": 1, "size": 3379, "failed": 0}],
    "slowest": [{"url": "https://example.com/site.css", "type": "css",
                 "status": 200, "size": 3379, "total_ms": 330,
                 "starttransfer_ms": 320}],
    "total_size": 3379,
    "error": null
  },
  "cross_checks": [
    {"severity": "info", "message": "у статических ресурсов нет cache-control"}
  ]
}
```

Каждая секция имеет поле `error` (`null` = ок). Пустой список ресурсов —
валидный результат, а не ошибка.

## Структура

```
web_checker.py           # тонкая обёртка
webcheck/                # пакет анализа
  constants.py           # VERSION, дефолты, пороги
  urls.py                # URL, IDN, дедупликация, кодировки
  extract.py             # HTMLParser + CSS url()/@import
  fetch.py               # curl -w: тайминги, заголовки, редиректы, тело
  analyze.py             # разбивка фаз, сводки, топ медленных
  checks.py              # перекрёстные проверки
  report.py              # человекочитаемый отчёт (RU)
  json_export.py         # машиночитаемый отчёт (--json)
  core.py                # оркестрация: страница -> ресурсы -> волны CSS
  cli.py                 # argparse, main(), выбор секций
tests/                   # юнит-тесты без сети + интеграционные (маркер)
pyproject.toml           # упаковка, версия, pytest, ruff
.github/workflows/ci.yml # CI: матрица 3.9-3.13, lint + тесты + smoke
LICENSE / NOTICE         # GPL-3.0-or-later
CHANGELOG.md             # история изменений
RELEASING.md             # процесс выпуска версий
CONTRIBUTING.md          # как участвовать в разработке
```

Направление зависимостей одностороннее: `cli -> core -> (fetch, extract,
analyze, checks) -> urls/constants`. Новая проверка = функция в `checks.py`,
новый тип ресурса = ветка в `extract.py` + тест.

## Тестирование

- **Юнит-тесты** (по умолчанию, `pytest`): `curl` замокан, сеть не нужна,
  стабильны в CI. Фикстуры только на generic-доменах (`example.com`).
- **Интеграционные тесты** (вручную, `pytest -m integration`): реальный
  запрос к `example.com`.

```
pytest                 # юниты
pytest -m integration  # интеграции (ходьба в сеть)
pytest -m ""           # всё вместе
```

## Участие в разработке

См. [CONTRIBUTING.md](CONTRIBUTING.md).

## Идеи и предложения

Есть идея, чего не хватает? Открывайте issue — новые проверки, режимы
(например, переиспользование соединений через `curl --parallel`), форматы
выгрузки и интеграции приветствуются.

## Лицензия

GPL-3.0-or-later. См. [LICENSE](LICENSE) и [NOTICE](NOTICE).
