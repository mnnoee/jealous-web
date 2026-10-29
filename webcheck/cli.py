"""CLI: argparse, main(). Один флаг на секцию (= чекбоксы UI)."""

import argparse
import sys

from . import core, json_export, report
from .constants import (
    DEFAULT_CSS_DEPTH,
    DEFAULT_TIMEOUT,
    DEFAULT_TOP,
    DEFAULT_WORKERS,
    FILTER_TYPES,
    USER_AGENT,
    VERSION,
)
from .urls import prepare_url

SECTION_RUNNERS = ('page', 'assets')


def build_parser():
    ap = argparse.ArgumentParser(
        description='Проверка страницы и всех её ресурсов: тайминги, размеры, '
                    'заголовки, эвристики. По умолчанию - обе секции.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            'Примеры:\n'
            '  jealous-web https://example.com\n'
            '  jealous-web example.com --page            # только страница\n'
            '  jealous-web example.com --assets          # только ресурсы\n'
            '  jealous-web example.com --filter css,js,font\n'
            '  jealous-web example.com --diagram\n'
            '  jealous-web example.com --json report.json\n'
        ))
    ap.add_argument('--version', action='version',
                    version=f'%(prog)s {VERSION}')
    ap.add_argument('url', help='URL страницы (схема необязательна)')
    ap.add_argument('--page', action='store_true', help='секция страницы')
    ap.add_argument('--assets', action='store_true',
                    help='секция ресурсов (js/css/img/font/...)')
    ap.add_argument('--all', action='store_true', help='включить все секции')
    ap.add_argument('-j', '--workers', type=int, default=DEFAULT_WORKERS,
                    metavar='N',
                    help=f'параллельных загрузок (по умолчанию {DEFAULT_WORKERS})')
    ap.add_argument('-t', '--timeout', type=float, default=DEFAULT_TIMEOUT,
                    metavar='SEC',
                    help=f'таймаут на запрос, сек (по умолчанию {DEFAULT_TIMEOUT:g})')
    ap.add_argument('--css-depth', type=int, default=DEFAULT_CSS_DEPTH,
                    metavar='N',
                    help='глубина раскрытия @import/url() в CSS '
                         f'(по умолчанию {DEFAULT_CSS_DEPTH})')
    ap.add_argument('--filter', default='', metavar='LIST',
                    help='типы ресурсов через запятую, например: css,js,img,font; '
                         f'доступны: {", ".join(FILTER_TYPES)}')
    ap.add_argument('--top', type=int, default=DEFAULT_TOP, metavar='N',
                    help=f'сколько медленных ресурсов показывать (по умолчанию '
                         f'{DEFAULT_TOP})')
    ap.add_argument('--no-http2', action='store_true',
                    help='не просить HTTP/2')
    ap.add_argument('--insecure', action='store_true',
                    help='не проверять TLS-сертификат (как httpstat)')
    ap.add_argument('--no-compress', action='store_true',
                    help='не просить сжатие (Accept-Encoding: identity)')
    ap.add_argument('--user-agent', default=USER_AGENT, metavar='UA',
                    help=f'User-Agent (по умолчанию {USER_AGENT})')
    ap.add_argument('--diagram', action='store_true',
                    help='печатать httpstat-диаграммы по каждому запросу')
    ap.add_argument('--json', nargs='?', const='report.json', metavar='PATH',
                    help='записать машиночитаемый JSON-отчёт '
                         '(по умолчанию report.json)')
    return ap


def _selected(args):
    selected = [name for name in SECTION_RUNNERS if getattr(args, name)]
    if args.all or not selected:
        return list(SECTION_RUNNERS)
    return selected


def _type_filter(value):
    types = {item.strip().lower() for item in (value or '').split(',')
             if item.strip()}
    return types or None


def main(argv=None):
    ap = build_parser()
    args = ap.parse_args(argv)

    sections, found_checks, elapsed = core.run(
        prepare_url(args.url),
        workers=args.workers,
        timeout=args.timeout,
        http2=not args.no_http2,
        insecure=args.insecure,
        compress=not args.no_compress,
        user_agent=args.user_agent,
        css_depth=args.css_depth,
        type_filter=_type_filter(args.filter),
        run_sections=_selected(args),
        top=args.top,
    )

    print(report.build_report(args.url, sections, found_checks,
                              top=args.top, diagram=args.diagram))

    if args.json:
        path = json_export.write_json_report(
            args.url, sections, args.json, found_checks, elapsed)
        print(f'\nJSON-отчёт записан в: {path}', file=sys.stderr)


if __name__ == '__main__':
    main()
