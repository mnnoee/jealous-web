"""Производные метрики: разбивка таймингов, типы, самые медленные."""

from .constants import DEFAULT_TOP


def ms(seconds):
    """Секунды -> целые миллисекунды (curl отдаёт секунды)."""
    return round(float(seconds or 0) * 1000)


def human_size(size):
    size = int(size or 0)
    if size < 1024:
        return f'{size}B'
    if size < 1024 * 1024:
        return f'{size / 1024:.1f}K'
    return f'{size / 1024 / 1024:.1f}M'


def breakdown(timings):
    """Разложить тайминги curl на фазы (в мс).

    redirect - отдельно: время редиректов пересекается с dns/tcp/tls
    последующих запросов, поэтому сумму фаз сравнивать с total нельзя.
    """
    timings = timings or {}
    dns = ms(timings.get('time_namelookup'))
    connect = ms(timings.get('time_connect'))
    appconnect = ms(timings.get('time_appconnect'))
    pretransfer = ms(timings.get('time_pretransfer'))
    starttransfer = ms(timings.get('time_starttransfer'))
    total = ms(timings.get('time_total'))

    return {
        'dns': dns,
        'tcp': max(0, connect - dns) if connect else 0,
        'tls': max(0, appconnect - connect) if appconnect else 0,
        'redirect': ms(timings.get('time_redirect')),
        'ttfb': max(0, starttransfer - pretransfer),
        'transfer': max(0, total - starttransfer),
        'total': total,
    }


def is_css(result):
    """CSS ли это по content-type или расширению (серверы врут и так, и так)."""
    content_type = (result.content_type or '').lower()
    if 'css' in content_type:
        return True
    path = (result.final_url or '').lower().split('?')[0]
    return path.endswith('.css')


def by_type(results):
    """Сводка по типам: количество, переданные байты, число ошибок."""
    groups = {}
    for result in results:
        name = result.rtype or 'other'
        group = groups.setdefault(name, {
            'type': name, 'count': 0, 'size': 0, 'failed': 0})
        group['count'] += 1
        if result.error:
            group['failed'] += 1
        else:
            group['size'] += int(result.size or 0)
    return sorted(groups.values(), key=lambda g: (-g['size'], g['type']))


def slowest(results, top=DEFAULT_TOP):
    """Топ медленных по total; ошибки не участвуют."""
    ok = [r for r in results if not r.error]
    ok.sort(key=lambda r: r.timings.get('time_total', 0.0), reverse=True)
    return [
        {
            'url': r.url,
            'type': r.rtype or 'other',
            'status': r.status,
            'size': int(r.size or 0),
            'total_ms': ms(r.timings.get('time_total')),
            'starttransfer_ms': ms(r.timings.get('time_starttransfer')),
        }
        for r in ok[:top]
    ]


def result_dict(result):
    """FetchResult -> сериализуемый элемент отчёта (ресурс или страница)."""
    return {
        'url': result.url,
        'final_url': result.final_url,
        'type': result.rtype,
        'status': result.status,
        'http_version': result.http_version,
        'content_type': result.content_type,
        'size': int(result.size or 0),
        'timings_ms': breakdown(result.timings),
        'redirects': result.redirects,
        'headers': result.headers,
        'error': result.error,
    }
