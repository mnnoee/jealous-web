# jealous-web

[![CI](https://github.com/mnnoee/jealous-web/actions/workflows/ci.yml/badge.svg)](https://github.com/mnnoee/jealous-web/actions/workflows/ci.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-0.1.1-green.svg)](CHANGELOG.md)

> Part of the [Jealous Moon](https://github.com/mnnoee) toolkit — offline
> server and domain diagnostics.

Check one web page and **every resource it references**: httpstat-style timings
(DNS / TCP / TLS / TTFB / transfer), transfer sizes, HTTP version, headers,
redirects and heuristic cross-checks. Not a crawler: it opens a single page and
follows only what is actually mentioned in HTML and CSS.

> [README на русском](README.ru.md) — полная документация.

## Features

- **Page section** (`--page`): status, HTTP version, content type, transferred
  bytes, remote IP:port, redirect chain, phase timings, selected headers.
- **Assets section** (`--assets`): `script`, `link` (stylesheet / modulepreload
  / preload with `as` / icon / manifest), `img` and `srcset`, `source`,
  `video`/`audio`/`track`/`embed`, `object`, `iframe`, `poster`, inline
  `<style>` and `style=""`, `url()` and `@import` inside CSS.
- **CSS waves**: references from CSS are expanded recursively
  (`--css-depth`, default 3), including external `@import`.
- **Realistic request**: `Accept-Encoding` (gzip/br), HTTP/2, own User-Agent,
  optional `--insecure`.
- **Wire sizes**: sizes are bytes actually transferred (compressed), not the
  decompressed HTML.
- **Charset handling**: header or `<meta charset>`, so windows-1251 pages do
  not produce broken URLs.
- **Cross-checks**: missing HSTS, uncompressed text, duplicate headers,
  4xx/5xx assets, mixed content, third-party hosts, heavy assets, slow TTFB,
  HTTP/1.1, missing `cache-control`.
- **Section isolation**: a failed page fetch puts `error` in the section, the
  report and JSON are still produced.
- **IDN**: Cyrillic and other non-ASCII hosts are converted to punycode.
- JSON export (`--json [PATH]`): `meta` + `page` + `assets` + `cross_checks`.

> **Note:** findings are heuristics, not verdicts. Each resource is fetched by
> its own `curl` process, so DNS/TCP/TLS show the cost of a **new** connection,
> not a browser-reused one. JS is not executed: SPA pages will look empty.
> Page bodies larger than 5 MB are not parsed.

## Install

Not on PyPI yet (planned). Install straight from GitHub:

```bash
pip install git+https://github.com/mnnoee/jealous-web.git
```

Or run straight from a clone:

```bash
python3 web_checker.py example.com
```

Requires `curl` with HTTP/2 support (check `curl --version`).

## Usage

```bash
jealous-web example.com                     # page + all resources
jealous-web example.com --page              # page only
jealous-web example.com --assets            # resources only
jealous-web example.com --filter css,js,font
jealous-web example.com --diagram           # httpstat diagrams
jealous-web example.com --json out.json     # machine-readable report
jealous-web --help                          # all options
```

The scheme may be omitted: `https://` is assumed.

## Example report

```
--- Страница ---
  статус:      200
  HTTP:        2
  размер:      12.1K (передано)
  DNS:         7 ms
  TCP:         60 ms
  TLS:         65 ms
  TTFB:        250 ms
  передача:    30 ms
  всего:       395 ms

--- Ресурсы (3) ---
STAT  TYPE         VER        DNS   TCP   TLS  TTFB  TOTAL     SIZE  URL
 200  css          HTTP/2      18    61    64   190    330     3.3K  https://example.com/site.css
 200  js           HTTP/2      19    62    65   191    331     1.0K  https://example.com/app.js
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

GPL-3.0-or-later. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
