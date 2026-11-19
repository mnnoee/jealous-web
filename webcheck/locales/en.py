"""English string catalog."""

CATALOG = {
    # CLI
    "cli.desc": "Check a page and all of its resources: timings, sizes, "
                "headers, heuristics. Both sections by default.",
    "cli.epilog": (
        "Examples:\n"
        "  jealous-web https://example.com\n"
        "  jealous-web example.com --page            # page only\n"
        "  jealous-web example.com --assets          # resources only\n"
        "  jealous-web example.com --filter css,js,font\n"
        "  jealous-web example.com --diagram\n"
        "  jealous-web example.com --json report.json\n"
    ),
    "cli.url": "page URL (the scheme is optional)",
    "cli.page": "page section",
    "cli.assets": "resources section (js/css/img/font/...)",
    "cli.all": "enable all sections",
    "cli.workers": "parallel downloads (default {n})",
    "cli.timeout": "request timeout, seconds (default {n})",
    "cli.css_depth": "CSS @import/url() expansion depth (default {n})",
    "cli.filter": "comma-separated resource types, for example: css,js,img,font; "
                  "available: {types}",
    "cli.top": "how many slow resources to show (default {n})",
    "cli.no_http2": "do not request HTTP/2",
    "cli.insecure": "do not verify the TLS certificate (like httpstat)",
    "cli.no_compress": "do not request compression (Accept-Encoding: identity)",
    "cli.user_agent": "User-Agent (default {ua})",
    "cli.diagram": "print httpstat diagrams for every request",
    "cli.check_up": "print cross-checks and notes",
    "cli.json": "write a machine-readable JSON report (default report.json)",
    "cli.lang": "output language: auto | ru | en (default auto - from the locale)",
    "cli.json_written": "\nJSON report written to: {path}",

    # core
    "core.no_body": "the page body was not received or it is not HTML/CSS - "
                    "there is nothing to extract resources from",
    "core.html_parse": "failed to parse HTML: {err}",
    "core.page_not_loaded": "the page was not loaded: {err}",

    # checks
    "chk.status": "the page responds with status {status}",
    "chk.http_only": "the page stays on HTTP after redirects (no HTTPS)",
    "chk.no_hsts": "no HSTS (Strict-Transport-Security)",
    "chk.hsts_short": "HSTS max-age={age} s is less than 180 days",
    "chk.no_compression": "text response without compression (no content-encoding)",
    "chk.http11": "the page is served over HTTP/1.1 (the server did not offer HTTP/2)",
    "chk.redirects": "{n} redirect(s) before the page",
    "chk.duplicate_headers": "duplicate response headers: {names}",
    "chk.missing_security": "missing security headers: {names}",
    "chk.slow_ttfb": "TTFB {ttfb} ms - the server responds slower than {limit} ms",
    "chk.assets_failed": "{n} resources failed to load (for example, {url})",
    "chk.assets_bad": "resources with status >= 400: {n} "
                      "(for example, {status} {url})",
    "chk.bot_high": "anti-bot protection (JS challenge/CAPTCHA)",
    "chk.bot_possible": "possible anti-bot protection",
    "chk.no_assets_bot": "no resources found: probably an anti-bot stub",
    "chk.no_assets": "no resources found in HTML "
                     "(perhaps JS loads them{filter_hint})",
    "chk.filter_hint": " or --filter narrowed it",
    "chk.heavy_page": "the page pulls {size} - more than {limit}",
    "chk.mixed_content": "mixed content: {n} resource(s) over HTTP "
                         "on an HTTPS page",
    "chk.third_party": "third-party hosts: {hosts}",
    "chk.no_cache_control": "static resources have no cache-control",
    "chk.big_assets": "{n} resource(s) heavier than {limit} "
                      "(heaviest: {size} {url})",

    # report
    "rep.page": "--- Page ---",
    "rep.error_line": "  [error] {msg}",
    "rep.status": "  status:      {v}",
    "rep.http": "  HTTP:        {v}",
    "rep.final": "  final:       {v}",
    "rep.type": "  type:        {v}",
    "rep.size": "  size:        {v} (transferred)",
    "rep.remote": "  remote:      {v}",
    "rep.redirects": "  redirects:   {n} ({chain})",
    "rep.dns": "  DNS:         {v} ms",
    "rep.tcp": "  TCP:         {v} ms",
    "rep.tls": "  TLS:         {v} ms",
    "rep.ttfb": "  TTFB:        {v} ms",
    "rep.transfer": "  transfer:    {v} ms",
    "rep.total": "  total:       {v} ms",
    "rep.bot_high": "  protection:  anti-bot protection (JS challenge/CAPTCHA)",
    "rep.bot_possible": "  protection:  possible anti-bot protection",
    "rep.not_specified": "(not specified)",
    "rep.assets": "--- Resources ({n}) ---",
    "rep.nothing_found": "  (nothing found)",
    "rep.by_type": "--- By type ---",
    "rep.slowest": "--- Slowest (top {n}) ---",
    "rep.checks": "--- Checks ---",
    "rep.diagrams": "--- Diagrams ---",
    "rep.note1": "* every resource is fetched by its own curl process: DNS/TCP/TLS are",
    "rep.note2": "  the cost of a new connection, not a browser-reused one",
    "rep.note3": "* size is transferred bytes (compressed); a snapshot at check time",
}
