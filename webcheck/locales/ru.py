"""Русский каталог строк."""

CATALOG = {
    # CLI
    "cli.desc": "Проверка страницы и всех её ресурсов: тайминги, размеры, "
                "заголовки, эвристики. По умолчанию - обе секции.",
    "cli.epilog": (
        "Примеры:\n"
        "  jealous-web https://example.com\n"
        "  jealous-web example.com --page            # только страница\n"
        "  jealous-web example.com --assets          # только ресурсы\n"
        "  jealous-web example.com --filter css,js,font\n"
        "  jealous-web example.com --diagram\n"
        "  jealous-web example.com --json report.json\n"
    ),
    "cli.url": "URL страницы (схема необязательна)",
    "cli.page": "секция страницы",
    "cli.assets": "секция ресурсов (js/css/img/font/...)",
    "cli.all": "включить все секции",
    "cli.workers": "параллельных загрузок (по умолчанию {n})",
    "cli.timeout": "таймаут на запрос, сек (по умолчанию {n})",
    "cli.css_depth": "глубина раскрытия @import/url() в CSS (по умолчанию {n})",
    "cli.filter": "типы ресурсов через запятую, например: css,js,img,font; "
                  "доступны: {types}",
    "cli.top": "сколько медленных ресурсов показывать (по умолчанию {n})",
    "cli.no_http2": "не просить HTTP/2",
    "cli.insecure": "не проверять TLS-сертификат (как httpstat)",
    "cli.no_compress": "не просить сжатие (Accept-Encoding: identity)",
    "cli.user_agent": "User-Agent (по умолчанию {ua})",
    "cli.diagram": "печатать httpstat-диаграммы по каждому запросу",
    "cli.check_up": "печатать перекрёстные проверки и пояснения",
    "cli.json": "записать машиночитаемый JSON-отчёт (по умолчанию report.json)",
    "cli.lang": "язык вывода: auto | ru | en (по умолчанию auto - по локали)",
    "cli.json_written": "\nJSON-отчёт записан в: {path}",

    # ядро
    "core.no_body": "тело страницы не получено или это не HTML/CSS - "
                    "ресурсы не из чего достать",
    "core.html_parse": "не удалось разобрать HTML: {err}",
    "core.page_not_loaded": "страница не загружена: {err}",

    # проверки
    "chk.status": "страница отвечает статусом {status}",
    "chk.http_only": "после редиректов страница остаётся на HTTP (нет HTTPS)",
    "chk.no_hsts": "нет HSTS (Strict-Transport-Security)",
    "chk.hsts_short": "HSTS max-age={age} с - меньше 180 дней",
    "chk.no_compression": "текстовый ответ без сжатия (нет content-encoding)",
    "chk.http11": "страница отдаётся по HTTP/1.1 (сервер не предложил HTTP/2)",
    "chk.redirects": "до страницы {n} редирект(ов)",
    "chk.duplicate_headers": "дублируются заголовки ответа: {names}",
    "chk.missing_security": "нет заголовков безопасности: {names}",
    "chk.slow_ttfb": "TTFB {ttfb} ms - сервер отвечает медленнее {limit} ms",
    "chk.assets_failed": "не загрузилось ресурсов: {n} (например, {url})",
    "chk.assets_bad": "ресурсы со статусом >= 400: {n} "
                      "(например, {status} {url})",
    "chk.bot_high": "антибот-защита (JS challenge/CAPTCHA)",
    "chk.bot_possible": "возможно, антибот-защита",
    "chk.no_assets_bot": "ресурсы не найдены: вероятно, антибот-заглушка",
    "chk.no_assets": "в HTML не найдено ресурсов "
                     "(возможно, их подгружает JS{filter_hint})",
    "chk.filter_hint": " или его сузил --filter",
    "chk.heavy_page": "страница тянет {size} - больше {limit}",
    "chk.mixed_content": "смешанный контент: {n} ресурс(ов) по HTTP "
                         "на HTTPS-странице",
    "chk.third_party": "сторонние хосты: {hosts}",
    "chk.no_cache_control": "у статических ресурсов нет cache-control",
    "chk.big_assets": "{n} ресурс(ов) тяжелее {limit} "
                      "(самый: {size} {url})",

    # отчёт
    "rep.page": "--- Страница ---",
    "rep.error_line": "  [ошибка] {msg}",
    "rep.status": "  статус:      {v}",
    "rep.http": "  HTTP:        {v}",
    "rep.final": "  финальный:   {v}",
    "rep.type": "  тип:         {v}",
    "rep.size": "  размер:      {v} (передано)",
    "rep.remote": "  удалённый:   {v}",
    "rep.redirects": "  редиректы:   {n} ({chain})",
    "rep.dns": "  DNS:         {v} ms",
    "rep.tcp": "  TCP:         {v} ms",
    "rep.tls": "  TLS:         {v} ms",
    "rep.ttfb": "  TTFB:        {v} ms",
    "rep.transfer": "  передача:    {v} ms",
    "rep.total": "  всего:       {v} ms",
    "rep.bot_high": "  защита:      антибот-защита (JS challenge/CAPTCHA)",
    "rep.bot_possible": "  защита:      возможно, антибот-защита",
    "rep.not_specified": "(не указан)",
    "rep.assets": "--- Ресурсы ({n}) ---",
    "rep.nothing_found": "  (ничего не найдено)",
    "rep.by_type": "--- По типам ---",
    "rep.slowest": "--- Самые медленные (до {n}) ---",
    "rep.checks": "--- Проверки ---",
    "rep.diagrams": "--- Диаграммы ---",
    "rep.note1": "* каждый ресурс качается отдельным процессом curl: "
                 "DNS/TCP/TLS -",
    "rep.note2": "  цена нового соединения, а не переиспользованного браузером",
    "rep.note3": "* размер - переданные байты (со сжатием); "
                 "это срез на момент проверки",
}
