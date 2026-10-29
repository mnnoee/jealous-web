"""Unit-тесты: перекрёстные проверки страницы и ресурсов."""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from webcheck.checks import run_checks
from webcheck.constants import BIG_ASSET_BYTES, HEAVY_PAGE_BYTES
from webcheck.fetch import FetchResult


def _page(**overrides):
    page = {
        'url': 'https://example.com/',
        'final_url': 'https://example.com/',
        'status': 200,
        'http_version': '2',
        'content_type': 'text/html; charset=utf-8',
        'size': 10_000,
        'timings_ms': {'ttfb': 100, 'total': 300},
        'redirects': [],
        'headers': {
            'strict-transport-security': ['max-age=31536000'],
            'content-encoding': ['gzip'],
            'x-content-type-options': ['nosniff'],
            'referrer-policy': ['strict-origin-when-cross-origin'],
            'content-security-policy': ["default-src 'self'"],
            'cache-control': ['max-age=3'],
        },
        'error': None,
    }
    page.update(overrides)
    return page


def _result(url='https://example.com/a.css', rtype='css', status=200,
            size=1024, error=None, headers=None, final_url=None):
    result = FetchResult(url, rtype)
    result.final_url = final_url or url
    result.status = status
    result.size = size
    result.error = error
    if headers is None:
        headers = {'cache-control': ['public, max-age=2592000']}
    result.headers = headers
    return result


def _messages(checks):
    return ' | '.join(check['message'] for check in checks)


class CleanPageTest(unittest.TestCase):
    def test_clean_page_has_no_findings(self):
        self.assertEqual(run_checks(_page()), [])

    def test_error_page_skips_checks(self):
        self.assertEqual(run_checks({'error': 'down'}), [])


class PageChecksTest(unittest.TestCase):
    def test_bad_status(self):
        found = run_checks(_page(status=404))
        self.assertIn('статусом 404', _messages(found))

    def test_http_final(self):
        found = run_checks(_page(final_url='http://example.com/'))
        self.assertIn('остаётся на HTTP', _messages(found))

    def test_no_hsts(self):
        page = _page(headers={'content-encoding': ['gzip']})
        found = run_checks(page)
        self.assertIn('нет HSTS', _messages(found))

    def test_short_hsts(self):
        found = run_checks(_page(
            headers={'strict-transport-security': ['max-age=3600']}))
        self.assertEqual(found[0]['severity'], 'info')
        self.assertIn('max-age=3600', found[0]['message'])

    def test_no_compression(self):
        page = _page(headers={})
        found = run_checks(page)
        self.assertIn('без сжатия', _messages(found))

    def test_http1(self):
        found = run_checks(_page(http_version='1.1'))
        self.assertIn('HTTP/1.1', _messages(found))

    def test_redirects(self):
        found = run_checks(_page(redirects=[
            {'status': 301, 'location': 'https://example.com/'}]))
        self.assertIn('1 редирект', _messages(found))

    def test_duplicate_headers(self):
        page = _page(headers={
            'strict-transport-security': ['max-age=1', 'max-age=2'],
            'content-encoding': ['br'],
        })
        found = run_checks(page)
        self.assertIn('дублируются заголовки', _messages(found))
        self.assertIn('strict-transport-security', _messages(found))

    def test_security_headers_missing(self):
        found = run_checks(_page(headers={'content-encoding': ['gzip']}))
        text = _messages(found)
        self.assertIn('referrer-policy', text)
        self.assertIn('content-security-policy', text)

    def test_slow_ttfb(self):
        found = run_checks(_page(timings_ms={'ttfb': 900, 'total': 1200}))
        self.assertIn('TTFB 900 ms', _messages(found))


class AssetChecksTest(unittest.TestCase):
    def test_failed_asset(self):
        found = run_checks(_page(), [_result(error='timeout')])
        self.assertIn('не загрузилось ресурсов: 1', _messages(found))

    def test_bad_asset_status(self):
        found = run_checks(_page(), [_result(status=404)])
        self.assertIn('статусом >= 400: 1', _messages(found))

    def test_no_assets(self):
        found = run_checks(_page(), [])
        self.assertIn('не найдено ресурсов', _messages(found))
        self.assertEqual(found[0]['severity'], 'info')

    def test_no_assets_with_filter_hint(self):
        found = run_checks(_page(), [], has_filter=True)
        self.assertIn('--filter', _messages(found))

    def test_heavy_page(self):
        found = run_checks(_page(), [_result(size=HEAVY_PAGE_BYTES + 1)])
        self.assertIn('тянет', _messages(found))

    def test_mixed_content(self):
        found = run_checks(_page(), [
            _result(url='http://example.com/a.css',
                    final_url='http://example.com/a.css')])
        self.assertIn('смешанный контент', _messages(found))

    def test_third_party_host(self):
        found = run_checks(_page(), [
            _result(url='https://cdn.example.net/a.css')])
        self.assertIn('сторонние хосты: cdn.example.net', _messages(found))

    def test_static_without_cache_control(self):
        found = run_checks(_page(), [_result(headers={})])
        self.assertIn('нет cache-control', _messages(found))

    def test_big_asset(self):
        found = run_checks(_page(), [_result(size=BIG_ASSET_BYTES + 1)])
        self.assertIn('тяжелее', _messages(found))
        self.assertEqual(found[-1]['severity'], 'info')

    def test_own_host_not_third_party(self):
        found = run_checks(_page(), [_result(url='https://example.com/a.css')])
        self.assertNotIn('сторонние хосты', _messages(found))
