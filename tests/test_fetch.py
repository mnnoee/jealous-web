"""Unit-тесты: curl-обёртка, заголовки, тело, флаги (без сети)."""

import os
import subprocess
import sys
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from webcheck.fetch import FetchResult, fetch, parse_curl_output, parse_header_blocks


class FakeProc:
    def __init__(self, returncode=0, stdout=b'', stderr=b''):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _payload(**overrides):
    data = {
        'time_namelookup': 0.01,
        'time_connect': 0.02,
        'time_appconnect': 0.03,
        'time_pretransfer': 0.04,
        'time_redirect': 0.0,
        'time_starttransfer': 0.05,
        'time_total': 0.06,
        'num_redirects': 0,
        'http_version': '2',
        'http_code': 200,
        'size_download': 1234,
        'size_header': 100,
        'url_effective': 'https://example.com/',
        'scheme': 'https',
        'remote_ip': '203.0.113.10',
        'remote_port': '443',
        'content_type': 'text/html; charset=utf-8',
    }
    data.update(overrides)
    return data


def _fake_run(payload=None, headers='', body=b'', returncode=0, stderr=b''):
    def run(cmd, **kwargs):
        header_path = cmd[cmd.index('-D') + 1]
        body_path = cmd[cmd.index('-o') + 1]
        with open(header_path, 'w', encoding='utf-8') as f:
            f.write(headers)
        with open(body_path, 'wb') as f:
            f.write(body)
        import json
        return FakeProc(returncode, json.dumps(payload or _payload()).encode(),
                        stderr)
    return run


class HeaderParseTest(unittest.TestCase):
    def test_redirect_chain_and_final(self):
        text = (
            'HTTP/1.1 301 Moved Permanently\r\n'
            'Location: https://example.com/a\r\n'
            '\r\n'
            'HTTP/2 200\r\n'
            'Content-Type: text/html\r\n'
            'Cache-Control: a\r\n'
            'Cache-Control: b\r\n'
            '\r\n'
        )
        blocks = parse_header_blocks(text)
        self.assertEqual([status for status, _ in blocks], [301, 200])
        self.assertEqual(blocks[-1][1]['cache-control'], ['a', 'b'])

    def test_informational_skipped(self):
        text = ('HTTP/1.1 100 Continue\r\n\r\n'
                'HTTP/2 200\r\nServer: nginx\r\n\r\n')
        blocks = parse_header_blocks(text)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0][0], 200)

    def test_obs_fold(self):
        text = 'HTTP/2 200\r\nContent-Security-Policy: default-src\r\n  \'self\'\r\n\r\n'
        blocks = parse_header_blocks(text)
        self.assertEqual(blocks[0][1]['content-security-policy'],
                         ["default-src 'self'"])

    def test_broken_kept_partially(self):
        blocks = parse_header_blocks('not a header\r\n\r\n')
        self.assertEqual(blocks, [])


class CurlOutputTest(unittest.TestCase):
    def test_json(self):
        self.assertEqual(parse_curl_output('{"http_code": 200}'),
                         {'http_code': 200})

    def test_garbage(self):
        self.assertIsNone(parse_curl_output('<html>'))
        self.assertIsNone(parse_curl_output('[]'))


class FetchSuccessTest(unittest.TestCase):
    def test_fields_and_redirects(self):
        headers = (
            'HTTP/1.1 301 Moved Permanently\r\n'
            'Location: https://example.com/\r\n\r\n'
            'HTTP/2 200\r\n'
            'Content-Type: text/html; charset=utf-8\r\n'
            'Server: nginx\r\n\r\n'
        )
        payload = _payload(num_redirects=1, time_redirect=0.01)
        with mock.patch('webcheck.fetch.subprocess.run',
                        side_effect=_fake_run(payload, headers, b'<html>hi</html>')):
            result = fetch('http://example.com/', rtype='page')
        self.assertIsNone(result.error)
        self.assertEqual(result.status, 200)
        self.assertEqual(result.http_version, '2')
        self.assertEqual(result.final_url, 'https://example.com/')
        self.assertEqual(result.size, 1234)
        self.assertEqual(result.scheme, 'https')
        self.assertEqual(result.remote_ip, '203.0.113.10')
        self.assertEqual(result.redirects,
                         [{'status': 301, 'location': 'https://example.com/'}])
        self.assertEqual(result.headers['server'], ['nginx'])
        self.assertEqual(result.body, b'<html>hi</html>')

    def test_body_not_kept_for_images(self):
        payload = _payload(content_type='image/png')
        with mock.patch('webcheck.fetch.subprocess.run',
                        side_effect=_fake_run(payload, body=b'png')):
            result = fetch('https://example.com/a.png')
        self.assertIsNone(result.body)

    def test_timings_are_floats(self):
        with mock.patch('webcheck.fetch.subprocess.run', side_effect=_fake_run()):
            result = fetch('https://example.com/')
        self.assertAlmostEqual(result.timings['time_total'], 0.06)


class FetchFlagsTest(unittest.TestCase):
    def _capture(self, **kwargs):
        captured = {}

        def run(cmd, **extra):
            captured['cmd'] = cmd
            return _fake_run()(cmd, **extra)

        with mock.patch('webcheck.fetch.subprocess.run', side_effect=run):
            fetch('https://example.com/', **kwargs)
        return captured['cmd']

    def test_default_flags(self):
        cmd = self._capture()
        self.assertIn('--compressed', cmd)
        self.assertIn('--http2', cmd)
        self.assertIn('--proto', cmd)
        self.assertIn('=http,https', cmd)
        self.assertEqual(cmd[-1], 'https://example.com/')
        ua_index = cmd.index('-A') + 1
        self.assertTrue(cmd[ua_index].startswith('jealous-web/'))

    def test_plain_http(self):
        cmd = self._capture(http2=False, compress=False)
        self.assertNotIn('--http2', cmd)
        self.assertNotIn('--compressed', cmd)
        self.assertIn('Accept-Encoding: identity', cmd)

    def test_insecure(self):
        self.assertIn('-k', self._capture(insecure=True))


class FetchFailuresTest(unittest.TestCase):
    def test_nonzero_exit_takes_last_stderr_line(self):
        proc = FakeProc(7, b'', b'line one\ncurl: (7) Failed to connect\n')
        with mock.patch('webcheck.fetch.subprocess.run', return_value=proc):
            result = fetch('https://example.com/')
        self.assertEqual(result.error, 'curl: (7) Failed to connect')

    def test_timeout(self):
        with mock.patch('webcheck.fetch.subprocess.run',
                        side_effect=subprocess.TimeoutExpired('curl', 5)):
            result = fetch('https://example.com/', timeout=5)
        self.assertIn('timeout', result.error)

    def test_curl_missing(self):
        with mock.patch('webcheck.fetch.subprocess.run',
                        side_effect=FileNotFoundError):
            result = fetch('https://example.com/')
        self.assertEqual(result.error, 'curl not found in PATH')

    def test_bad_json(self):
        proc = FakeProc(0, b'not json', b'')
        with mock.patch('webcheck.fetch.subprocess.run', return_value=proc):
            result = fetch('https://example.com/')
        self.assertIn('cannot parse', result.error)


class FetchResultTest(unittest.TestCase):
    def test_defaults(self):
        result = FetchResult('https://example.com/', 'css')
        self.assertEqual(result.final_url, 'https://example.com/')
        self.assertEqual(result.redirects, [])
        self.assertEqual(result.headers, {})
        self.assertIsNone(result.body)
