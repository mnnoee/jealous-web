"""Unit-тесты: JSON-экспорт - схема, meta, totals, cross_checks."""

import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from webcheck.constants import VERSION
from webcheck.json_export import build_json, write_json_report


def _sections():
    page = {
        'url': 'https://example.com/',
        'final_url': 'https://example.com/',
        'type': 'page',
        'status': 200,
        'http_version': '2',
        'content_type': 'text/html',
        'size': 100,
        'timings_ms': {'total': 300},
        'headers': {},
        'error': None,
    }
    items = [
        {'url': 'https://example.com/a.css', 'size': 50, 'error': None},
        {'url': 'https://example.com/b.css', 'size': 0, 'error': 'timeout'},
    ]
    assets = {
        'items': items,
        'by_type': [],
        'slowest': [],
        'total_size': 50,
        'error': None,
    }
    return {'page': page, 'assets': assets}


class JsonExportTest(unittest.TestCase):
    def test_schema_shape(self):
        doc = build_json('https://example.com/', _sections(), [
            {'severity': 'warning', 'message': 'x'},
        ], elapsed=1.5)

        self.assertEqual(doc['meta']['version'], VERSION)
        self.assertEqual(doc['meta']['url'], 'https://example.com/')
        self.assertEqual(doc['meta']['final_url'], 'https://example.com/')
        self.assertEqual(doc['meta']['sections_run'], ['page', 'assets'])
        self.assertEqual(doc['meta']['elapsed_sec'], 1.5)
        self.assertIn('checked_at', doc['meta'])
        self.assertEqual(doc['cross_checks'][0]['severity'], 'warning')

    def test_totals(self):
        meta = build_json('https://example.com/', _sections())['meta']
        self.assertEqual(meta['status'], 200)
        self.assertEqual(meta['resources_total'], 2)
        self.assertEqual(meta['resources_ok'], 1)
        self.assertEqual(meta['resources_failed'], 1)
        self.assertEqual(meta['bytes_total'], 150)

    def test_sections_run_matches_selected(self):
        doc = build_json('https://example.com/', {'page': _sections()['page']})
        self.assertEqual(doc['meta']['sections_run'], ['page'])
        self.assertNotIn('assets', doc)

    def test_empty_document(self):
        doc = build_json('https://example.com/', {})
        self.assertEqual(doc['meta']['sections_run'], [])
        self.assertEqual(doc['cross_checks'], [])

    def test_write_json_report(self):
        path = os.path.join(tempfile.mkdtemp(), 'out.json')
        written = write_json_report('https://example.com/', _sections(), path,
                                    [], 0.5)
        self.assertTrue(os.path.isabs(written))
        with open(written, encoding='utf-8') as f:
            doc = json.load(f)
        self.assertEqual(doc['meta']['resources_total'], 2)
        self.assertEqual(doc['page']['status'], 200)
