"""Unit-тесты: оркестрация страницы и ресурсов (fetch замокан)."""

import os
import sys
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from webcheck import core
from webcheck.fetch import FetchResult


def _result(url, rtype, body=b'', content_type='text/html', headers=None,
            error=None):
    result = FetchResult(url, rtype)
    result.final_url = url
    result.status = 200
    result.http_version = '2'
    result.content_type = content_type
    result.body = body or None
    result.size = len(body)
    result.error = error
    result.headers = headers or {}
    result.timings = {
        'time_namelookup': 0.01,
        'time_connect': 0.02,
        'time_appconnect': 0.03,
        'time_pretransfer': 0.04,
        'time_starttransfer': 0.05,
        'time_total': 0.06,
    }
    return result


HTML = ('<html><head>'
        '<link rel="stylesheet" href="/a.css">'
        '<script src="/app.js"></script>'
        '</head><body><img src="/i.png"></body></html>')

CSS = '@import "b.css"; .x { background: url(/f.woff2) }'


def _fake_fetch(responses):
    calls = []

    def run(url, *args, **kwargs):
        calls.append(url)
        if url not in responses:
            return _result(url, kwargs.get('rtype') or 'other',
                           content_type='application/octet-stream')
        return responses[url]

    run.calls = calls
    return run


class RunTest(unittest.TestCase):
    def _pages(self):
        return {
            'https://example.com/': _result(
                'https://example.com/', 'page', HTML.encode(),
                'text/html; charset=utf-8'),
            'https://example.com/a.css': _result(
                'https://example.com/a.css', 'css', CSS.encode(), 'text/css'),
            'https://example.com/b.css': _result(
                'https://example.com/b.css', 'css', b'.b{}', 'text/css'),
            'https://example.com/f.woff2': _result(
                'https://example.com/f.woff2', 'font', b'', 'font/woff2'),
            'https://example.com/i.png': _result(
                'https://example.com/i.png', 'img', b'', 'image/png'),
            'https://example.com/app.js': _result(
                'https://example.com/app.js', 'js', b'', 'application/javascript'),
        }

    def test_discovers_resources_and_css_wave(self):
        fake = _fake_fetch(self._pages())
        with mock.patch.object(core, 'fetch', side_effect=fake):
            sections, checks, elapsed = core.run('https://example.com/')

        self.assertIn('page', sections)
        self.assertEqual(sections['page']['status'], 200)
        kinds = {item['type'] for item in sections['assets']['items']}
        self.assertEqual(kinds, {'css', 'js', 'img', 'font'})
        urls = {item['url'] for item in sections['assets']['items']}
        self.assertIn('https://example.com/b.css', urls)
        self.assertIn('https://example.com/f.woff2', urls)
        self.assertGreaterEqual(elapsed, 0)
        self.assertIsInstance(checks, list)

    def test_filter_applies_to_all_waves(self):
        fake = _fake_fetch(self._pages())
        with mock.patch.object(core, 'fetch', side_effect=fake):
            sections, _, _ = core.run(
                'https://example.com/', type_filter={'css'})
        kinds = {item['type'] for item in sections['assets']['items']}
        self.assertEqual(kinds, {'css'})

    def test_dedup_by_normalized_url(self):
        pages = self._pages()
        fake = _fake_fetch(pages)
        with mock.patch.object(core, 'fetch', side_effect=fake):
            sections, _, _ = core.run('https://example.com/')
        urls = [item['url'] for item in sections['assets']['items']]
        self.assertEqual(len(urls), len(set(urls)))

    def test_base_href(self):
        html = ('<base href="https://cdn.example.net/assets/">'
                '<link rel="stylesheet" href="a.css">')
        pages = {
            'https://example.com/': _result(
                'https://example.com/', 'page', html.encode()),
            'https://cdn.example.net/assets/a.css': _result(
                'https://cdn.example.net/assets/a.css', 'css', b'', 'text/css'),
        }
        fake = _fake_fetch(pages)
        with mock.patch.object(core, 'fetch', side_effect=fake):
            sections, _, _ = core.run('https://example.com/')
        self.assertEqual(sections['assets']['items'][0]['url'],
                         'https://cdn.example.net/assets/a.css')

    def test_page_error_isolated(self):
        failed = _result('https://example.com/', 'page', error='curl: (6) resolve failed')
        fake = _fake_fetch({'https://example.com/': failed})
        with mock.patch.object(core, 'fetch', side_effect=fake):
            sections, checks, _ = core.run('https://example.com/')
        self.assertIn('resolve failed', sections['page']['error'])
        self.assertIn('страница не загружена', sections['assets']['error'])
        self.assertEqual(checks, [])

    def test_no_body_gives_asset_error(self):
        pages = {'https://example.com/': _result(
            'https://example.com/', 'page', b'', 'application/octet-stream')}
        fake = _fake_fetch(pages)
        with mock.patch.object(core, 'fetch', side_effect=fake):
            sections, checks, _ = core.run('https://example.com/')
        self.assertIsNotNone(sections['assets']['error'])
        self.assertEqual(sections['assets']['items'], [])
        # проверки страницы остаются, но проверок по ресурсам нет
        messages = ' | '.join(check['message'] for check in checks)
        self.assertNotIn('не найдено ресурсов', messages)

    def test_page_only_section(self):
        fake = _fake_fetch(self._pages())
        with mock.patch.object(core, 'fetch', side_effect=fake):
            sections, _, _ = core.run(
                'https://example.com/', run_sections=('page',))
        self.assertEqual(list(sections), ['page'])
        self.assertEqual(len(fake.calls), 1)

    def test_assets_only_section(self):
        fake = _fake_fetch(self._pages())
        with mock.patch.object(core, 'fetch', side_effect=fake):
            sections, _, _ = core.run(
                'https://example.com/', run_sections=('assets',))
        self.assertEqual(list(sections), ['assets'])
        self.assertTrue(sections['assets']['items'])

    def test_checks_use_page_data(self):
        pages = self._pages()
        pages['https://example.com/'].headers = {}  # нет HSTS и безопасности
        fake = _fake_fetch(pages)
        with mock.patch.object(core, 'fetch', side_effect=fake):
            _, checks, _ = core.run('https://example.com/')
        messages = ' | '.join(check['message'] for check in checks)
        self.assertIn('нет HSTS', messages)
