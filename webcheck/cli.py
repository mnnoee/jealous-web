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
from .i18n import prescan_argv, set_lang, t
from .urls import prepare_url

SECTION_RUNNERS = ('page', 'assets')


def build_parser():
    ap = argparse.ArgumentParser(
        description=t('cli.desc'),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=t('cli.epilog'))
    ap.add_argument('--version', action='version',
                    version=f'%(prog)s {VERSION}')
    ap.add_argument('url', help=t('cli.url'))
    ap.add_argument('--page', action='store_true', help=t('cli.page'))
    ap.add_argument('--assets', action='store_true', help=t('cli.assets'))
    ap.add_argument('--all', action='store_true', help=t('cli.all'))
    ap.add_argument('-j', '--workers', type=int, default=DEFAULT_WORKERS,
                    metavar='N',
                    help=t('cli.workers', n=DEFAULT_WORKERS))
    ap.add_argument('-t', '--timeout', type=float, default=DEFAULT_TIMEOUT,
                    metavar='SEC',
                    help=t('cli.timeout', n=f'{DEFAULT_TIMEOUT:g}'))
    ap.add_argument('--css-depth', type=int, default=DEFAULT_CSS_DEPTH,
                    metavar='N',
                    help=t('cli.css_depth', n=DEFAULT_CSS_DEPTH))
    ap.add_argument('--filter', default='', metavar='LIST',
                    help=t('cli.filter', types=', '.join(FILTER_TYPES)))
    ap.add_argument('--top', type=int, default=DEFAULT_TOP, metavar='N',
                    help=t('cli.top', n=DEFAULT_TOP))
    ap.add_argument('--no-http2', action='store_true',
                    help=t('cli.no_http2'))
    ap.add_argument('--insecure', action='store_true',
                    help=t('cli.insecure'))
    ap.add_argument('--no-compress', action='store_true',
                    help=t('cli.no_compress'))
    ap.add_argument('--user-agent', default=USER_AGENT, metavar='UA',
                    help=t('cli.user_agent', ua=USER_AGENT))
    ap.add_argument('--diagram', action='store_true',
                    help=t('cli.diagram'))
    ap.add_argument('--check-up', action='store_true', dest='check_up',
                    help=t('cli.check_up'))
    ap.add_argument('--json', nargs='?', const='report.json', metavar='PATH',
                    help=t('cli.json'))
    ap.add_argument('--lang', choices=('auto', 'ru', 'en'), default='auto',
                    help=t('cli.lang'))
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
    argv = list(sys.argv[1:] if argv is None else argv)
    set_lang(prescan_argv(argv))
    ap = build_parser()
    args = ap.parse_args(argv)
    set_lang(args.lang)

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
                              top=args.top, diagram=args.diagram,
                              check_up=args.check_up))

    if args.json:
        path = json_export.write_json_report(
            args.url, sections, args.json, found_checks, elapsed)
        print(t('cli.json_written', path=path), file=sys.stderr)


if __name__ == '__main__':
    main()
