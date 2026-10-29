"""JSON-экспорт: машиночитаемый отчёт (как в остальных модулях набора)."""

import datetime
import json
import os

from .constants import VERSION

SECTION_ORDER = ('page', 'assets')


def _totals(sections):
    page = sections.get('page') or {}
    items = ((sections.get('assets') or {}).get('items') or [])
    ok = [item for item in items if not item.get('error')]
    return {
        'status': page.get('status'),
        'http_version': page.get('http_version'),
        'bytes_page': int(page.get('size') or 0),
        'resources_total': len(items),
        'resources_ok': len(ok),
        'resources_failed': len(items) - len(ok),
        'bytes_total': int(page.get('size') or 0)
        + sum(int(item.get('size') or 0) for item in ok),
    }


def build_json(url, sections, checks=None, elapsed=0.0):
    """Собрать dict-отчёт: meta + секции + cross_checks."""
    page = sections.get('page') or {}
    doc = {
        'meta': {
            'version': VERSION,
            'url': url,
            'final_url': page.get('final_url') or url,
            'checked_at': datetime.datetime.now(
                datetime.timezone.utc).isoformat(),
            'elapsed_sec': round(float(elapsed or 0), 3),
            'sections_run': [key for key in SECTION_ORDER if key in sections],
        },
    }
    doc['meta'].update(_totals(sections))
    for key in SECTION_ORDER:
        if key in sections:
            doc[key] = sections[key]
    doc['cross_checks'] = list(checks or [])
    return doc


def write_json_report(url, sections, path='report.json', checks=None,
                      elapsed=0.0):
    """Записать отчёт и вернуть абсолютный путь."""
    doc = build_json(url, sections, checks, elapsed)
    full = os.path.abspath(path)
    with open(full, 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False, indent=2, default=str)
    return full
