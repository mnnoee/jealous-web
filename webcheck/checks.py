"""Перекрёстные проверки страницы и ресурсов (без новых запросов).

Формат совпадает с остальными модулями: [{"severity": "info"|"warning",
"message": "..."}]. Вывод - эвристика: повод проверить, а не приговор.
"""

from .analyze import human_size
from .constants import (
    BIG_ASSET_BYTES,
    HEAVY_PAGE_BYTES,
    HSTS_MIN_MAX_AGE,
    SLOW_TTFB_MS,
    STATIC_TYPES,
)
from .urls import host_of

_SEVERITY_LABEL = {'warning': '[warning]', 'info': '[info]'}


def _values(page, name):
    return (page.get('headers') or {}).get(name) or []


def _header(page, name):
    values = _values(page, name)
    return values[0] if values else None


def _max_age(hsts):
    """max-age=... из HSTS (секунды) или None."""
    for part in (hsts or '').split(';'):
        key, _, value = part.strip().partition('=')
        if key.lower() == 'max-age':
            try:
                return int(value.strip().strip('"'))
            except ValueError:
                return None
    return None


def _asset_header(result, name):
    values = (result.headers or {}).get(name) or []
    return values[0] if values else None


def run_checks(page, assets=None, has_filter=False):
    """Проверить уже собранные данные. assets - список FetchResult или None."""
    if not page or page.get('error'):
        return []

    found = []

    def add(severity, message):
        found.append({'severity': severity, 'message': message})

    final_url = (page.get('final_url') or '').lower()
    is_https = final_url.startswith('https://')
    status = page.get('status') or 0

    # --- сама страница ---
    if not 200 <= status < 300:
        add('warning', f'страница отвечает статусом {status}')
    if final_url.startswith('http://'):
        add('warning', 'после редиректов страница остаётся на HTTP (нет HTTPS)')
    if is_https:
        hsts = _header(page, 'strict-transport-security')
        if not hsts:
            add('warning', 'нет HSTS (Strict-Transport-Security)')
        else:
            max_age = _max_age(hsts)
            if max_age is not None and max_age < HSTS_MIN_MAX_AGE:
                add('info', f'HSTS max-age={max_age} с - меньше 180 дней')

    content_type = (page.get('content_type') or '').lower()
    if ('text/' in content_type or 'json' in content_type) \
            and not _header(page, 'content-encoding'):
        add('warning', 'текстовый ответ без сжатия (нет content-encoding)')

    http_version = page.get('http_version')
    if http_version == '1.1':
        add('info', 'страница отдаётся по HTTP/1.1 (сервер не предложил HTTP/2)')

    redirects = page.get('redirects') or []
    if redirects:
        add('info', f'до страницы {len(redirects)} редирект(ов)')

    duplicates = sorted(
        name for name, values in (page.get('headers') or {}).items()
        if len(values) > 1 and name not in ('set-cookie', 'link'))
    if duplicates:
        add('warning', 'дублируются заголовки ответа: ' + ', '.join(duplicates[:6]))

    missing = [name for name in ('x-content-type-options', 'referrer-policy')
               if not _header(page, name)]
    if not _header(page, 'content-security-policy') \
            and not _header(page, 'x-frame-options'):
        missing.append('content-security-policy/x-frame-options')
    if missing:
        add('info', 'нет заголовков безопасности: ' + ', '.join(missing))

    ttfb = (page.get('timings_ms') or {}).get('ttfb') or 0
    if ttfb > SLOW_TTFB_MS:
        add('warning', f'TTFB {ttfb} ms - сервер отвечает медленнее {SLOW_TTFB_MS} ms')

    # --- ресурсы ---
    if assets is not None:
        ok = [r for r in assets if not r.error]
        failed = [r for r in assets if r.error]
        bad = [r for r in ok if r.status and not 200 <= r.status < 300]

        if failed:
            add('warning', f'не загрузилось ресурсов: {len(failed)} '
                           f'(например, {failed[0].url})')
        if bad:
            add('warning', f'ресурсы со статусом >= 400: {len(bad)} '
                           f'(например, {bad[0].status} {bad[0].url})')
        if not assets:
            tail = ' или его сузил --filter' if has_filter else ''
            add('info', 'в HTML не найдено ресурсов '
                        f'(возможно, их подгружает JS{tail})')

        page_bytes = int(page.get('size') or 0)
        total_bytes = page_bytes + sum(int(r.size or 0) for r in ok)
        if total_bytes > HEAVY_PAGE_BYTES:
            add('warning', f'страница тянет {human_size(total_bytes)} - '
                           f'больше {human_size(HEAVY_PAGE_BYTES)}')

        if is_https:
            mixed = [r for r in ok
                     if (r.final_url or '').lower().startswith('http://')]
            if mixed:
                add('warning', f'смешанный контент: {len(mixed)} ресурс(ов) '
                               f'по HTTP на HTTPS-странице')

        hosts = {host_of(r.final_url) for r in ok}
        own_host = host_of(page.get('final_url'))
        third_party = sorted(host for host in hosts if host and host != own_host)
        if third_party:
            shown = ', '.join(third_party[:5])
            if len(third_party) > 5:
                shown += f' (+{len(third_party) - 5})'
            add('info', 'сторонние хосты: ' + shown)

        static = [r for r in ok if (r.rtype or '') in STATIC_TYPES]
        if static and not any(_asset_header(r, 'cache-control') for r in static):
            add('info', 'у статических ресурсов нет cache-control')

        big = sorted((r for r in ok if int(r.size or 0) > BIG_ASSET_BYTES),
                     key=lambda r: int(r.size or 0), reverse=True)
        if big:
            add('info', f'{len(big)} ресурс(ов) тяжелее '
                        f'{human_size(BIG_ASSET_BYTES)} (самый: '
                        f'{human_size(big[0].size)} {big[0].url})')

    return found


def severity_label(severity):
    return _SEVERITY_LABEL.get(severity, f'[{severity}]')
