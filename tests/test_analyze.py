"""Unit-тесты: разбивка таймингов, сводки, сериализация."""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from webcheck.analyze import breakdown, by_type, human_size, is_css, result_dict, slowest


def _result(url, total=0.2, size=1024, rtype='css', error=None,
            content_type='text/css', starttransfer=0.1):
    from webcheck.fetch import FetchResult

    result = FetchResult(url, rtype)
    result.final_url = url
    result.status = 200
    result.size = size
    result.content_type = content_type
    result.error = error
    result.timings = {
        'time_total': total,
        'time_starttransfer': starttransfer,
        'time_namelookup': 0.01,
        'time_connect': 0.02,
        'time_appconnect': 0.03,
        'time_pretransfer': 0.04,
    }
    return result


class BreakdownTest(unittest.TestCase):
    def test_phases(self):
        timings = {
            'time_namelookup': 0.010,
            'time_connect': 0.070,
            'time_appconnect': 0.130,
            'time_pretransfer': 0.140,
            'time_starttransfer': 0.340,
            'time_total': 0.390,
        }
        b = breakdown(timings)
        self.assertEqual(b['dns'], 10)
        self.assertEqual(b['tcp'], 60)
        self.assertEqual(b['tls'], 60)
        self.assertEqual(b['ttfb'], 200)
        self.assertEqual(b['transfer'], 50)
        self.assertEqual(b['total'], 390)

    def test_no_tls(self):
        b = breakdown({'time_connect': 0.02, 'time_appconnect': 0.0,
                       'time_starttransfer': 0.05, 'time_total': 0.06})
        self.assertEqual(b['tls'], 0)
        self.assertEqual(b['redirect'], 0)

    def test_redirect_reported_separately(self):
        b = breakdown({'time_redirect': 0.25, 'time_total': 0.5})
        self.assertEqual(b['redirect'], 250)
        self.assertEqual(b['total'], 500)

    def test_empty(self):
        self.assertEqual(breakdown({})['total'], 0)


class HumanSizeTest(unittest.TestCase):
    def test_units(self):
        self.assertEqual(human_size(0), '0B')
        self.assertEqual(human_size(512), '512B')
        self.assertEqual(human_size(2048), '2.0K')
        self.assertEqual(human_size(3 * 1024 * 1024), '3.0M')


class IsCssTest(unittest.TestCase):
    def test_by_content_type(self):
        self.assertTrue(is_css(_result('https://example.com/x', content_type='text/css')))

    def test_by_extension(self):
        self.assertTrue(is_css(_result('https://example.com/x.css?v=1',
                                       content_type='text/plain')))

    def test_not_css(self):
        self.assertFalse(is_css(_result('https://example.com/x.js',
                                        content_type='application/javascript')))


class ByTypeTest(unittest.TestCase):
    def test_groups_and_failed(self):
        items = [
            _result('https://example.com/a.css', size=100),
            _result('https://example.com/b.css', size=200),
            _result('https://example.com/c.js', size=50, rtype='js',
                    content_type='application/javascript'),
            _result('https://example.com/d.png', rtype='img', error='boom'),
        ]
        groups = {g['type']: g for g in by_type(items)}
        self.assertEqual(groups['css']['count'], 2)
        self.assertEqual(groups['css']['size'], 300)
        self.assertEqual(groups['img']['failed'], 1)
        self.assertEqual(groups['img']['size'], 0)

    def test_sorted_by_size(self):
        items = [_result('https://example.com/a.js', rtype='js', size=10),
                 _result('https://example.com/a.png', rtype='img', size=100)]
        self.assertEqual([g['type'] for g in by_type(items)], ['img', 'js'])


class SlowestTest(unittest.TestCase):
    def test_order_and_limit(self):
        items = [
            _result('https://example.com/a', total=0.1),
            _result('https://example.com/b', total=0.5),
            _result('https://example.com/c', total=0.3),
        ]
        top = slowest(items, 2)
        self.assertEqual([item['url'] for item in top],
                         ['https://example.com/b', 'https://example.com/c'])
        self.assertEqual(top[0]['total_ms'], 500)

    def test_errors_excluded(self):
        items = [_result('https://example.com/a', total=1.0, error='x'),
                 _result('https://example.com/b', total=0.1)]
        self.assertEqual([i['url'] for i in slowest(items)], ['https://example.com/b'])


class ResultDictTest(unittest.TestCase):
    def test_shape(self):
        doc = result_dict(_result('https://example.com/a.css'))
        for key in ('url', 'final_url', 'type', 'status', 'http_version',
                    'content_type', 'size', 'timings_ms', 'redirects',
                    'headers', 'error'):
            self.assertIn(key, doc)
        self.assertEqual(doc['type'], 'css')
        self.assertEqual(doc['timings_ms']['total'], 200)
