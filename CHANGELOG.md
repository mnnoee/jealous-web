# Changelog

Все заметные изменения проекта документируются в этом файле.

Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/),
версионирование — [Semantic Versioning](https://semver.org/lang/ru/).

## [Unreleased]

## [0.1.0] — 2026-10-29

### Added
- Первый публичный релиз: проверка страницы и всех её ресурсов.
- Секции `page` и `assets` (флаги `--page` / `--assets`, по умолчанию обе).
- Тайминги в стиле `httpstat`: DNS, TCP, TLS, TTFB, передача, редиректы,
  итог — для страницы и для каждого ресурса.
- Извлечение ресурсов из HTML: `script`, `link` (stylesheet / modulepreload /
  preload с `as` / icon / manifest), `img` и `srcset`, `source`,
  `video`/`audio`/`track`/`embed`, `object`, `iframe`, `poster`.
- Извлечение ссылок из CSS (`url()`, `@import`) с рекурсивным раскрытием
  волнами (`--css-depth`, по умолчанию 3).
- Inline-`<style>` и атрибуты `style=""`.
- Загрузка через `curl`: сжатие (`gzip`/`br`), HTTP/2, свой User-Agent,
  `--insecure`, `--no-compress`, `--no-http2`.
- Размеры — переданные байты (со сжатием), а не распакованное тело.
- Разбор заголовков и цепочки редиректов из `curl -D`.
- Кодировки: charset из заголовка, `<meta charset>` и BOM.
- IDN-хосты переводятся в punycode на сетевой границе.
- Перекрёстные проверки (`cross_checks`): HSTS, сжатие, дублирующиеся
  заголовки, 4xx/5xx ресурсы, смешанный контент, сторонние хосты, тяжёлые
  ресурсы, медленный TTFB, HTTP/1.1, отсутствие `cache-control`.
- Изоляция секций: ошибка загрузки страницы не роняет отчёт.
- Машиночитаемый JSON-отчёт (`--json [PATH]`) с `meta`, `page`, `assets`
  и `cross_checks`.
- `httpstat`-диаграммы по флагу `--diagram`.
- Упаковка проекта: `pyproject.toml` (PEP 621), установка через
  `pip install jealous-web` и консольная команда `jealous-web`.
- Лицензия GPL-3.0-or-later (`LICENSE`, `NOTICE`),
  `CHANGELOG.md`, `CONTRIBUTING.md`, `RELEASING.md`.
- Тесты: 118 юнит-тестов без сети (URL, извлечение, curl-обёртка, метрики,
  проверки, JSON, оркестрация, CLI) + 2 интеграционных (маркер `integration`).
- CI: матрица Python 3.9-3.13, ruff, pytest, smoke-тест CLI.

[Unreleased]: https://github.com/mnnoee/jealous-web/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/mnnoee/jealous-web/releases/tag/v0.1.0
