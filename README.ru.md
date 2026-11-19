# jealous-web

[![CI](https://github.com/mnnoee/jealous-web/actions/workflows/ci.yml/badge.svg)](https://github.com/mnnoee/jealous-web/actions/workflows/ci.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-0.2.0-green.svg)](CHANGELOG.md)

> Часть набора [Jealous Moon](https://github.com/mnnoee) для диагностики серверов и доменов.

Проверка одной страницы и всех ресурсов, на которые она ссылается. Инструмент показывает тайминги в стиле httpstat (DNS, TCP, TLS, TTFB, передача), переданные размеры, HTTP-версию, заголовки, редиректы и эвристические перекрёстные проверки. Это не краулер. Открывается одна страница и только то, что реально упомянуто в HTML и CSS.

> [README in English](README.md)

## Возможности

- **Секция страницы** (`--page`): статус, HTTP-версия, тип контента, переданные байты, удалённый IP:порт, цепочка редиректов, тайминги по фазам и выбранные заголовки.
- **Секция ресурсов** (`--assets`): script, link (stylesheet, modulepreload, preload с `as`, icon, manifest), img и srcset, source, video/audio/track/embed, object, iframe, poster, inline `<style>` и `style=""`.
- **Волны CSS** для `url()` и `@import`, рекурсивно до `--css-depth` (по умолчанию 3).
- **Реалистичные запросы** со сжатием, HTTP/2, своим User-Agent и необязательным `--insecure`.
- **Переданные размеры**, а не распакованное тело.
- **Кодировки** из заголовка, `<meta charset>` или BOM, чтобы страницы windows-1251 не давали битые ссылки.
- **Перекрёстные проверки**: HSTS, сжатие, дублирующиеся заголовки, заголовки безопасности, ресурсы 4xx/5xx, смешанный контент, сторонние хосты, тяжёлые ресурсы, медленный TTFB, HTTP/1.1 и отсутствие `cache-control`.
- **Детект антибот-защиты**. JS-челленджи и CAPTCHA распознаются, результат помечается как неполный.
- **Изоляция секций**. Ошибка загрузки страницы попадает в `error` секции, отчёт и JSON всё равно формируются.
- **IDN**. Не-ASCII хосты переводятся в punycode на сетевой границе.
- **Русский и английский интерфейс** (`--lang`).
- **JSON-экспорт** (`--json [PATH]`) с `meta`, `page`, `assets` и `cross_checks`.

## Требования

- Python 3.9 или новее.
- `curl` с поддержкой HTTP/2. Проверить можно через `curl --version`.

У Python-пакета нет сторонних зависимостей.

## Установка

Пока не на PyPI (публикация планируется). Установка напрямую с GitHub:

```bash
pip install git+https://github.com/mnnoee/jealous-web.git
```

Или запуск прямо из клона:

```bash
python3 web_checker.py example.com
```

После установки доступна команда `jealous-web`.

## Использование

```bash
jealous-web example.com                     # страница и все ресурсы
jealous-web example.com --page              # только страница
jealous-web example.com --assets            # только ресурсы
jealous-web example.com --filter css,js,font
jealous-web example.com --css-depth 1
jealous-web example.com --diagram           # httpstat-диаграммы
jealous-web example.com --check-up          # проверки и пояснения
jealous-web example.com --json out.json     # машиночитаемый отчёт
jealous-web --help                          # все опции
```

Схему можно не указывать. Без неё подставляется `https://`.

## Опции

| Флаг | Описание |
|------|----------|
| `--page` | секция страницы |
| `--assets` | секция ресурсов |
| `--all` | обе секции, поведение по умолчанию |
| `-j`, `--workers N` | параллельных загрузок, по умолчанию 10 |
| `-t`, `--timeout SEC` | таймаут на запрос, по умолчанию 20 |
| `--css-depth N` | глубина раскрытия `@import` и `url()`, по умолчанию 3 |
| `--filter LIST` | типы ресурсов, например `css,js,img,font` |
| `--top N` | сколько медленных ресурсов показывать, по умолчанию 10 |
| `--no-http2` | не просить HTTP/2 |
| `--no-compress` | запросить `Accept-Encoding: identity` |
| `--insecure` | не проверять TLS-сертификат |
| `--user-agent UA` | свой User-Agent |
| `--diagram` | печатать httpstat-диаграммы |
| `--check-up` | печатать проверки и пояснения |
| `--json [PATH]` | JSON-отчёт, по умолчанию `report.json` |
| `--lang auto\|ru\|en` | язык вывода, по умолчанию `auto` по локали |

## Что проверяется

Страница:

- код статуса, HTTP-версия, тип контента и переданный размер;
- цепочка редиректов и финальный URL;
- тайминги DNS, TCP, TLS, TTFB, передачи и общего времени;
- HSTS и его `max-age`, сжатие, дублирующиеся заголовки;
- заголовки безопасности, HTTP/1.1, медленный TTFB;
- страницы с антибот-защитой и JS-челленджем.

Ресурсы:

- ошибки загрузки и статусы 4xx/5xx;
- смешанный контент на HTTPS-странице;
- сторонние хосты;
- `cache-control` у статических ресурсов;
- ресурсы тяжелее 500 КБ;
- общий вес страницы больше 2 МБ.

Все выводы - эвристика, а не приговор. Каждый ресурс качается отдельным процессом `curl`, поэтому DNS, TCP и TLS показывают цену нового соединения, а не переиспользованного браузером.

## Антибот-защита

Некоторые сайты отвечают `200 OK` и небольшим HTML-фрагментом, который проверяет браузер через JavaScript, cookie или CAPTCHA. Обычный HTTP-клиент такую проверку не проходит. Инструмент распознаёт типовые признаки и явно показывает это:

```text
  защита:      антибот-защита (JS challenge/CAPTCHA)
```

В этом случае тело страницы - не настоящая страница, а список ресурсов неполный. В JSON появляется `page.bot_protection` с уровнем (`high` или `possible`) и списком общих признаков. Названия сайтов не используются.

## Язык интерфейса

Язык вывода берётся из локали или задаётся флагом `--lang {auto,ru,en}`.

## Пример отчёта

```text
==================================================
https://example.com
==================================================

--- Страница ---
  статус:      200
  HTTP:        2
  финальный:   https://example.com/
  тип:         text/html; charset=utf-8
  размер:      12.0K (передано)
  удалённый:   203.0.113.10:443
  DNS:         8 ms
  TCP:         15 ms
  TLS:         25 ms
  TTFB:        15 ms
  передача:    0 ms
  всего:       63 ms
  server:      nginx
  encoding:    gzip

--- Ресурсы (2) ---
STAT  TYPE         VER        DNS   TCP   TLS  TTFB  TOTAL     SIZE  URL
------------------------------------------------------------------------
 200  css          HTTP/2       0     0     0     1      1      20B  https://example.com/a.css
 200  js           HTTP/2       0     0     0     1      1      19B  https://example.com/app.js
```

## JSON-отчёт

`--json [PATH]` пишет машиночитаемый отчёт. Без пути создаётся `report.json` в текущем каталоге. В отчёте четыре ключа верхнего уровня:

- `meta` с версией, URL, финальным URL, временем проверки, длительностью, списком секций, статусом, HTTP-версией, объёмами и счётчиками ресурсов.
- `page` со статусом, `timings_ms`, заголовками, редиректами и `bot_protection`.
- `assets` с `items`, `by_type`, `slowest`, `total_size` и `error`.
- `cross_checks` с `severity` и `message` для каждой находки.

`page.bot_protection` появляется только при детекте антибот-страницы. В нём уровень (`high` или `possible`) и список общих признаков.

## Структура проекта

```text
web_checker.py          тонкая CLI-обёртка
webcheck/
  __init__.py           версия пакета
  constants.py          версия, дефолты, пороги
  i18n.py               определение языка и t()
  locales/
    ru.py               русские строки
    en.py               английские строки
  cli.py                argparse и main()
  core.py               оркестрация страницы и ресурсов
  fetch.py              один запрос curl и его тайминги
  extract.py            ресурсы из HTML и CSS
  urls.py               URL-хелперы, IDN, дедупликация, кодировки
  analyze.py            фазы, типы, самые медленные, размеры
  checks.py             перекрёстные проверки
  bot.py                детект антибот-защиты и JS-челленджей
  report.py             человекочитаемый отчёт
  json_export.py        JSON-экспорт
tests/                  юнит-тесты без сети
```

## Тесты

```bash
python -m pytest                 # юнит-тесты без сети
pytest -m integration            # живые проверки, по умолчанию отключены
ruff check .
```

Интеграционные тесты ходят в сеть и помечены маркером `integration`.

## Ограничения

- JavaScript не исполняется. SPA-страницы будут выглядеть почти пустыми.
- Антибот-страницы HTTP-клиент пройти не может. Они распознаются и помечаются как неполный результат.
- Тела страниц больше 5 МБ не разбираются.
- Тайминги ресурсов включают новое соединение на каждый ресурс.
- Выводы - эвристика. Это повод проверить дальше, а не финальный вердикт.

## Участие в разработке

См. [CONTRIBUTING.md](CONTRIBUTING.md).

## Лицензия

GPL-3.0-or-later. Подробности в [LICENSE](LICENSE) и [NOTICE](NOTICE).
