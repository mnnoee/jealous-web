"""Оркестрация: страница -> HTML -> ресурсы -> волны CSS -> проверки."""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from . import checks, extract
from .analyze import by_type, result_dict, slowest
from .constants import DEFAULT_CSS_DEPTH, DEFAULT_TIMEOUT, DEFAULT_TOP, DEFAULT_WORKERS, USER_AGENT
from .fetch import FetchResult, fetch
from .urls import decode_body, guess_type, make_absolute, normalize

ASSET_SECTIONS = ('page', 'assets')


def page_section(main):
    """FetchResult страницы -> секция отчёта."""
    data = result_dict(main)
    data['type'] = 'page'
    data.update({
        'scheme': main.scheme,
        'remote_ip': main.remote_ip,
        'remote_port': main.remote_port,
        'num_redirects': main.num_redirects,
    })
    return data


def _error_page(url, error):
    return {
        'url': url,
        'final_url': url,
        'type': 'page',
        'status': None,
        'http_version': None,
        'content_type': '',
        'size': 0,
        'timings_ms': {},
        'redirects': [],
        'headers': {},
        'error': error,
    }


def _resolve_type(url, rtype):
    """Тип из разметки; для <source> и inline-CSS угадываем по расширению."""
    if rtype in (None, 'source'):
        guessed = guess_type(url)
        if guessed != 'other':
            return guessed
    return rtype or 'other'


def collect_assets(main, workers=DEFAULT_WORKERS, timeout=DEFAULT_TIMEOUT,
                   http2=True, insecure=False, compress=True,
                   user_agent=USER_AGENT, css_depth=DEFAULT_CSS_DEPTH,
                   type_filter=None):
    """Найти ресурсы в HTML и докачать их волнами (CSS раскрывается глубже).

    Возвращает (список FetchResult, ошибка или None).
    """
    if not main.body:
        return [], ('тело страницы не получено или это не HTML/CSS - '
                    'ресурсы не из чего достать')

    try:
        parser = extract.ResourceExtractor()
        parser.feed(decode_body(main.body, main.content_type))
    except Exception as exc:  # битый HTML не должен ронять отчёт
        return [], f'не удалось разобрать HTML: {exc}'

    base = main.final_url
    if parser.base_href:
        base = make_absolute(base, parser.base_href) or base

    seen = {normalize(main.final_url)}
    queue = []

    def add(href, rtype=None, page_base=base):
        absolute = make_absolute(page_base, href)
        if not absolute:
            return
        key = normalize(absolute)
        if key in seen:
            return
        seen.add(key)
        kind = _resolve_type(absolute, rtype)
        if type_filter and kind not in type_filter:
            return
        queue.append((absolute, kind))

    for href, rtype in parser.resources:
        add(href, rtype)
    for css in parser.inline_styles:
        for url in extract.extract_css_refs(css):
            add(url)
    for style_attr in parser.style_attrs:
        for url in extract.extract_css_refs(style_attr):
            add(url)

    items = []
    for depth in range(css_depth + 1):
        if not queue:
            break
        next_queue = []
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(fetch, url, timeout, http2, insecure, compress,
                            user_agent, kind): (url, kind)
                for url, kind in queue
            }
            for future in as_completed(futures):
                url, kind = futures[future]
                try:
                    result = future.result()
                except Exception as exc:
                    result = FetchResult(url, kind)
                    result.error = str(exc)
                items.append(result)

                if result.error or not result.body or depth >= css_depth:
                    continue
                if not _is_css(result):
                    continue
                css_text = decode_body(result.body, result.content_type)
                for sub in extract.extract_css_refs(css_text):
                    absolute = make_absolute(result.final_url, sub)
                    if not absolute:
                        continue
                    key = normalize(absolute)
                    if key in seen:
                        continue
                    seen.add(key)
                    sub_type = _resolve_type(absolute, None)
                    if type_filter and sub_type not in type_filter:
                        continue
                    next_queue.append((absolute, sub_type))
        queue = next_queue

    return items, None


def _is_css(result):
    content_type = (result.content_type or '').lower()
    if 'css' in content_type:
        return True
    return (result.final_url or '').lower().split('?')[0].endswith('.css')


def assets_section(items, error=None, top=DEFAULT_TOP):
    ok = [item for item in items if not item.error]
    # Потоки завершаются в произвольном порядке: сортируем по URL, чтобы
    # отчёт и JSON были воспроизводимы от прогона к прогону.
    ordered = sorted(items, key=lambda item: item.url)
    return {
        'items': [result_dict(item) for item in ordered],
        'by_type': by_type(ordered),
        'slowest': slowest(ordered, top),
        'total_size': sum(int(item.size or 0) for item in ok),
        'error': error,
    }


def run(url, workers=DEFAULT_WORKERS, timeout=DEFAULT_TIMEOUT, http2=True,
        insecure=False, compress=True, user_agent=USER_AGENT,
        css_depth=DEFAULT_CSS_DEPTH, type_filter=None,
        run_sections=ASSET_SECTIONS, top=DEFAULT_TOP):
    """Проверить страницу. Возвращает (sections, cross_checks, elapsed_sec).

    Секции изолированы: ошибка загрузки страницы не бросает исключение,
    а попадает в error соответствующей секции.
    """
    started = time.time()
    sections = {}

    main = fetch(url, timeout, http2, insecure, compress, user_agent,
                 rtype='page')
    if main.error:
        if 'page' in run_sections:
            sections['page'] = _error_page(url, main.error)
        if 'assets' in run_sections:
            sections['assets'] = assets_section(
                [], f'страница не загружена: {main.error}', top)
        return sections, [], time.time() - started

    page = page_section(main)
    if 'page' in run_sections:
        sections['page'] = page

    items = []
    asset_error = None
    if 'assets' in run_sections:
        items, asset_error = collect_assets(
            main, workers=workers, timeout=timeout, http2=http2,
            insecure=insecure, compress=compress, user_agent=user_agent,
            css_depth=css_depth, type_filter=type_filter)
        sections['assets'] = assets_section(items, asset_error, top)

    checked_assets = items if 'assets' in run_sections and not asset_error \
        else None
    return sections, checks.run_checks(
        page, checked_assets, has_filter=bool(type_filter)), \
        time.time() - started
