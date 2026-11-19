# jealous-web

[![CI](https://github.com/mnnoee/jealous-web/actions/workflows/ci.yml/badge.svg)](https://github.com/mnnoee/jealous-web/actions/workflows/ci.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-0.2.0-green.svg)](CHANGELOG.md)

> Part of the [Jealous Moon](https://github.com/mnnoee) toolkit for server and domain diagnostics.

Check one web page and every resource it references. The tool shows httpstat style timings (DNS, TCP, TLS, TTFB, transfer), transferred sizes, HTTP version, headers, redirects and heuristic cross-checks. It is not a crawler. It opens a single page and follows only what is actually mentioned in HTML and CSS.

> [README на русском](README.ru.md) - полная русская документация.

## Features

- **Page section** (`--page`) with status, HTTP version, content type, transferred bytes, remote IP:port, redirect chain, phase timings and selected headers.
- **Assets section** (`--assets`) with script, link (stylesheet, modulepreload, preload with `as`, icon, manifest), img and srcset, source, video/audio/track/embed, object, iframe, poster, inline `<style>` and `style=""`.
- **CSS waves** for `url()` and `@import`, expanded recursively up to `--css-depth` (default 3).
- **Realistic requests** with compression, HTTP/2, a custom User-Agent and an optional `--insecure` mode.
- **Transferred sizes**, not decompressed body sizes.
- **Charset handling** from the response header, `<meta charset>` or BOM, so windows-1251 pages do not produce broken URLs.
- **Cross-checks** for HSTS, compression, duplicate headers, security headers, 4xx/5xx assets, mixed content, third-party hosts, heavy assets, slow TTFB, HTTP/1.1 and missing `cache-control`.
- **Anti-bot detection**. JS challenge and CAPTCHA stubs are recognised and the result is explicitly marked as incomplete.
- **Section isolation**. A failed page fetch puts `error` into the section and the report and JSON are still produced.
- **IDN support**. Non-ASCII hosts are converted to punycode at the network boundary.
- **Russian and English interface** (`--lang`).
- **JSON export** (`--json [PATH]`) with `meta`, `page`, `assets` and `cross_checks`.

## Requirements

- Python 3.9 or newer.
- `curl` with HTTP/2 support. Check with `curl --version`.

The Python package has no third-party dependencies.

## Install

Not on PyPI yet (planned). Install straight from GitHub:

```bash
pip install git+https://github.com/mnnoee/jealous-web.git
```

Or run straight from a clone:

```bash
python3 web_checker.py example.com
```

After installation the `jealous-web` command is available.

## Usage

```bash
jealous-web example.com                     # page and all resources
jealous-web example.com --page              # page only
jealous-web example.com --assets            # resources only
jealous-web example.com --filter css,js,font
jealous-web example.com --css-depth 1
jealous-web example.com --diagram           # httpstat diagrams
jealous-web example.com --check-up          # cross-checks and notes
jealous-web example.com --json out.json     # machine-readable report
jealous-web --help                          # all options
```

The scheme can be omitted. `https://` is assumed.

## Options

| Flag | Description |
|------|-------------|
| `--page` | page section |
| `--assets` | resources section |
| `--all` | both sections, the default |
| `-j`, `--workers N` | parallel downloads, default 10 |
| `-t`, `--timeout SEC` | request timeout, default 20 |
| `--css-depth N` | CSS `@import` and `url()` expansion depth, default 3 |
| `--filter LIST` | resource types, for example `css,js,img,font` |
| `--top N` | how many slow resources to show, default 10 |
| `--no-http2` | do not request HTTP/2 |
| `--no-compress` | request `Accept-Encoding: identity` |
| `--insecure` | do not verify the TLS certificate |
| `--user-agent UA` | custom User-Agent |
| `--diagram` | print httpstat diagrams |
| `--check-up` | print cross-checks and notes |
| `--json [PATH]` | write a JSON report, default `report.json` |
| `--lang auto\|ru\|en` | output language, default `auto` from the locale |

## What is checked

Page checks:

- status code, HTTP version, content type and transferred size;
- redirect chain and final URL;
- DNS, TCP, TLS, TTFB, transfer and total timings;
- HSTS and its `max-age`, compression, duplicate headers;
- security headers, HTTP/1.1, slow TTFB;
- anti-bot or JS challenge pages.

Resource checks:

- failures and 4xx/5xx statuses;
- mixed content on HTTPS pages;
- third-party hosts;
- `cache-control` on static assets;
- assets heavier than 500 KB;
- total page weight above 2 MB.

All findings are heuristics, not verdicts. Each resource is fetched by its own `curl` process, so DNS, TCP and TLS show the cost of a new connection, not a browser-reused one.

## Anti-bot protection

Some sites answer with `200 OK` and a small HTML stub that checks the browser with JavaScript, cookies or CAPTCHA. A plain HTTP client cannot pass such a check. The tool detects typical signals and reports it explicitly:

```text
  protection:  anti-bot protection (JS challenge/CAPTCHA)
```

In this case the page body is not the real page and the resource list is incomplete. The JSON report includes `page.bot_protection` with a level (`high` or `possible`) and a list of generic signals. No site names are used.

## Interface language

The output language follows the locale or can be forced with `--lang {auto,ru,en}`.

## Example report

```text
==================================================
https://example.com
==================================================

--- Page ---
  status:      200
  HTTP:        2
  final:       https://example.com/
  type:        text/html; charset=utf-8
  size:        12.0K (transferred)
  remote:      203.0.113.10:443
  DNS:         8 ms
  TCP:         15 ms
  TLS:         25 ms
  TTFB:        15 ms
  transfer:    0 ms
  total:       63 ms
  server:      nginx
  encoding:    gzip

--- Resources (2) ---
STAT  TYPE         VER        DNS   TCP   TLS  TTFB  TOTAL     SIZE  URL
------------------------------------------------------------------------
 200  css          HTTP/2       0     0     0     1      1      20B  https://example.com/a.css
 200  js           HTTP/2       0     0     0     1      1      19B  https://example.com/app.js
```

## JSON report

`--json [PATH]` writes a machine-readable report. Without a path it writes `report.json` in the current directory. The report has four top-level keys:

- `meta` with version, URL, final URL, check time, elapsed seconds, sections run, status, HTTP version, byte totals and resource counts.
- `page` with status, `timings_ms`, headers, redirects and `bot_protection`.
- `assets` with `items`, `by_type`, `slowest`, `total_size` and `error`.
- `cross_checks` with `severity` and `message` for every finding.

`page.bot_protection` appears only when an anti-bot page is detected. It has a level (`high` or `possible`) and a list of generic signals.

## Project structure

```text
web_checker.py          thin CLI wrapper
webcheck/
  __init__.py           package version
  constants.py          version, defaults, thresholds
  i18n.py               locale detection and t()
  locales/
    ru.py               Russian strings
    en.py               English strings
  cli.py                argparse and main()
  core.py               page and resource orchestration
  fetch.py              one curl request and its timings
  extract.py            resources from HTML and CSS
  urls.py               URL helpers, IDN, dedup, charset
  analyze.py            phases, types, slowest, sizes
  checks.py             cross-checks
  bot.py                anti-bot and JS challenge detection
  report.py             human-readable report
  json_export.py        JSON export
tests/                  unit tests without network
```

## Tests

```bash
python -m pytest                 # unit tests, no network
pytest -m integration            # live checks, disabled by default
ruff check .
```

Integration tests require network access and are marked with the `integration` marker.

## Limitations

- JavaScript is not executed. SPA pages will look mostly empty.
- Anti-bot challenge pages cannot be passed by an HTTP client. They are detected and marked as incomplete.
- Page bodies larger than 5 MB are not parsed.
- Resource timings include a new connection per resource.
- The findings are heuristics. Use them as a reason to check further, not as a final verdict.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

GPL-3.0-or-later. See [LICENSE](LICENSE) and [NOTICE](NOTICE) for details.
