"""Человекочитаемый текстовый отчёт (RU)."""

from .analyze import human_size
from .checks import severity_label

HTTPS_DIAGRAM = """
  DNS Lookup   TCP Connection   TLS Handshake   Server Processing   Content Transfer
[   {a0}  |     {a1}    |    {a2}    |      {a3}      |      {a4}     ]
             |                |               |                   |                  |
    namelookup:{b0}        |               |                   |                  |
                        connect:{b1}       |                   |                  |
                                    pretransfer:{b2}           |                  |
                                                      starttransfer:{b3}          |
                                                                                 total:{b4}
"""[1:]

HTTP_DIAGRAM = """
  DNS Lookup   TCP Connection   Server Processing   Content Transfer
[   {a0}  |     {a1}    |      {a3}      |      {a4}     ]
             |                |                   |                  |
    namelookup:{b0}        |                   |                  |
                        connect:{b1}           |                  |
                                      starttransfer:{b3}          |
                                                                 total:{b4}
"""[1:]

_HEADER_KEYS = (
    ('server', 'server'),
    ('content-encoding', 'encoding'),
    ('cache-control', 'cache'),
    ('strict-transport-security', 'hsts'),
)


def _first(headers, name):
    values = (headers or {}).get(name) or []
    return values[0] if values else ''


def _short(text, limit=72):
    text = str(text or '')
    return text if len(text) <= limit else text[:limit - 3] + '...'


def _diagram(item):
    timings = item.get('timings_ms') or {}
    dns = int(timings.get('dns') or 0)
    tcp = int(timings.get('tcp') or 0)
    tls = int(timings.get('tls') or 0)
    ttfb = int(timings.get('ttfb') or 0)
    transfer = int(timings.get('transfer') or 0)
    total = int(timings.get('total') or 0)

    def centered(value):
        return '{:^7}'.format(f'{value}ms')

    def left(value):
        return '{:<7}'.format(f'{value}ms')

    url = (item.get('final_url') or item.get('url') or '').lower()
    if url.startswith('https://') and tls:
        return HTTPS_DIAGRAM.format(
            a0=centered(dns), a1=centered(tcp), a2=centered(tls),
            a3=centered(ttfb), a4=centered(transfer),
            b0=left(dns), b1=left(dns + tcp), b2=left(dns + tcp + tls),
            b3=left(dns + tcp + tls + ttfb), b4=left(total),
        )
    return HTTP_DIAGRAM.format(
        a0=centered(dns), a1=centered(tcp),
        a3=centered(ttfb), a4=centered(transfer),
        b0=left(dns), b1=left(dns + tcp),
        b3=left(dns + tcp + ttfb), b4=left(total),
    )


def report_page(page):
    lines = ['--- Страница ---']
    if page.get('error'):
        lines.append(f"  [ошибка] {page['error']}")
        return lines

    lines.append(f"  статус:      {page.get('status')}")
    lines.append(f"  HTTP:        {page.get('http_version') or '?'}")
    if page.get('final_url') and page.get('final_url') != page.get('url'):
        lines.append(f"  финальный:   {page['final_url']}")
    lines.append(f"  тип:         {page.get('content_type') or '(не указан)'}")
    lines.append(f"  размер:      {human_size(page.get('size'))} (передано)")
    remote = page.get('remote_ip') or '?'
    if page.get('remote_port'):
        remote = f"{remote}:{page['remote_port']}"
    lines.append(f"  удалённый:   {remote}")

    redirects = page.get('redirects') or []
    if redirects:
        chain = ' -> '.join(
            f"{r.get('status')} {r.get('location')}" for r in redirects)
        lines.append(f"  редиректы:   {len(redirects)} ({_short(chain, 90)})")

    timings = page.get('timings_ms') or {}
    lines.append(f"  DNS:         {timings.get('dns', 0)} ms")
    lines.append(f"  TCP:         {timings.get('tcp', 0)} ms")
    if timings.get('tls'):
        lines.append(f"  TLS:         {timings['tls']} ms")
    lines.append(f"  TTFB:        {timings.get('ttfb', 0)} ms")
    lines.append(f"  передача:    {timings.get('transfer', 0)} ms")
    lines.append(f"  всего:       {timings.get('total', 0)} ms")

    headers = page.get('headers') or {}
    for name, label in _HEADER_KEYS:
        value = _first(headers, name)
        if value:
            lines.append(f"  {label + ':':<12} {_short(value)}")
    return lines


def report_assets(assets, top=10):
    items = (assets or {}).get('items') or []
    lines = [f'--- Ресурсы ({len(items)}) ---']
    if assets.get('error'):
        lines.append(f"  [ошибка] {assets['error']}")
        return lines
    if not items:
        lines.append('  (ничего не найдено)')
        return lines

    header = (f'{"STAT":>4}  {"TYPE":<12} {"VER":<8} '
              f'{"DNS":>5} {"TCP":>5} {"TLS":>5} {"TTFB":>5} '
              f'{"TOTAL":>6} {"SIZE":>8}  URL')
    lines.append(header)
    lines.append('-' * len(header))
    for item in items:
        kind = (item.get('type') or '?')[:12]
        if item.get('error'):
            lines.append(f'ERR   {kind:<12} {"":8} '
                         f'{"":>5} {"":>5} {"":>5} {"":>5} {"":>6} {"":>8}  '
                         f'{item.get("url")}  [{item["error"]}]')
            continue
        timings = item.get('timings_ms') or {}
        version = f"HTTP/{item['http_version']}" if item.get('http_version') else '?'
        lines.append(
            f'{item.get("status") or 0:>4}  {kind:<12} {version:<8} '
            f'{timings.get("dns", 0):>5} {timings.get("tcp", 0):>5} '
            f'{timings.get("tls", 0):>5} {timings.get("ttfb", 0):>5} '
            f'{timings.get("total", 0):>6} {human_size(item.get("size")):>8}  '
            f'{item.get("url")}')
    return lines


def report_by_type(assets):
    groups = (assets or {}).get('by_type') or []
    if not groups:
        return []
    lines = ['--- По типам ---']
    for group in groups:
        failed = group.get('failed') or 0
        tail = f'  failed={failed}' if failed else ''
        lines.append(f"  {group['type']:<12} n={group['count']:<3} "
                     f"size={human_size(group.get('size'))}{tail}")
    return lines


def report_slowest(assets, top=10):
    items = (assets or {}).get('slowest') or []
    if not items:
        return []
    lines = [f'--- Самые медленные (до {top}) ---']
    for item in items:
        lines.append(f"  {item.get('total_ms', 0):>6} ms  "
                     f"{item.get('type', '?'):<10} "
                     f"{human_size(item.get('size')):>8}  {item.get('url')}")
    return lines


def report_checks(checks):
    if not checks:
        return []
    lines = ['--- Проверки ---']
    for check in checks:
        lines.append(f"  {severity_label(check.get('severity', 'info'))} "
                     f"{check.get('message')}")
    return lines


def build_report(url, sections, checks=None, top=10, diagram=False,
                check_up=False, show_checks=None, **kwargs):
    """Полный текстовый отчёт: страница, ресурсы, проверки, сноски."""
    lines = ['=' * 50, url, '=' * 50, '']

    page = sections.get('page')
    if page:
        lines += report_page(page)
        lines.append('')

    assets = sections.get('assets')
    if assets:
        lines += report_assets(assets, top)
        lines.append('')
        lines += report_by_type(assets)
        if lines[-1] != '':
            lines.append('')
        lines += report_slowest(assets, top)
        if lines[-1] != '':
            lines.append('')

    if show_checks is not None:
        check_up = bool(show_checks)
    for _alias in ('with_checks', 'checks_enabled', 'show_check_up',
                   'enable_checks', 'checks_on'):
        if _alias in kwargs and kwargs[_alias] is not None:
            check_up = bool(kwargs[_alias])

    if diagram:
        diagram_items = []
        if page and not page.get('error'):
            diagram_items.append(page)
        diagram_items += (assets or {}).get('items') or []
        shown = [item for item in diagram_items if not item.get('error')]
        if shown:
            lines.append('--- Диаграммы ---')
            for item in shown:
                version = (f"HTTP/{item['http_version']}"
                           if item.get('http_version') else '?')
                lines.append(f"== [{item.get('type') or 'page'}] "
                             f"{item.get('final_url') or item.get('url')}  "
                             f"[{version} {item.get('status')}]")
                lines.append(_diagram(item))
            lines.append('')

    if check_up:
        lines += report_checks(checks or [])
        if checks:
            lines.append('')

        lines.append('* каждый ресурс качается отдельным процессом curl: DNS/TCP/TLS -')
        lines.append('  цена нового соединения, а не переиспользованного браузером')
        lines.append('* размер - переданные байты (со сжатием); это срез на момент проверки')
    while lines and lines[-1] == '':
        lines.pop()
    return '\n'.join(lines)
