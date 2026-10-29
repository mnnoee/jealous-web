"""Unit-тесты: URL-утилиты, типы, декодирование тела."""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from webcheck.urls import decode_body, guess_type, host_of, make_absolute, normalize, prepare_url


class PrepareUrlTest(unittest.TestCase):
    def test_adds_https(self):
        self.assertEqual(prepare_url('example.com'), 'https://example.com')

    def test_keeps_scheme_and_path(self):
        self.assertEqual(prepare_url('http://example.com:8080/a?b=1'),
                         'http://example.com:8080/a?b=1')

    def test_idn_to_punycode(self):
        self.assertEqual(prepare_url('смешнявки.рф'),
                         'https://xn--b1afkhhhz2d6c.xn--p1ai')

    def test_idn_with_port(self):
        self.assertEqual(prepare_url('https://смешнявки.рф:8443/'),
                         'https://xn--b1afkhhhz2d6c.xn--p1ai:8443/')

    def test_empty(self):
        self.assertEqual(prepare_url('  '), '')


class MakeAbsoluteTest(unittest.TestCase):
    def test_relative(self):
        self.assertEqual(make_absolute('https://example.com/a/b.html', 'c.css'),
                         'https://example.com/a/c.css')

    def test_protocol_relative(self):
        self.assertEqual(make_absolute('https://example.com/', '//cdn.example.net/x.js'),
                         'https://cdn.example.net/x.js')

    def test_fragment_stripped(self):
        self.assertEqual(make_absolute('https://example.com/', '/a.css#x'),
                         'https://example.com/a.css')

    def test_service_schemes(self):
        for href in ('data:text/plain,hi', 'javascript:void(0)',
                     'mailto:a@example.com', 'blob:https://example.com/x'):
            self.assertIsNone(make_absolute('https://example.com/', href))

    def test_not_http(self):
        self.assertIsNone(make_absolute('https://example.com/', 'ftp://example.com/x'))

    def test_empty(self):
        self.assertIsNone(make_absolute('https://example.com/', '   '))


class NormalizeTest(unittest.TestCase):
    def test_trailing_slash(self):
        self.assertEqual(normalize('https://example.com/a/'),
                         normalize('https://example.com/a'))

    def test_host_case_and_query(self):
        self.assertEqual(normalize('https://EXAMPLE.com/a?x=1'),
                         normalize('https://example.com/a?x=1'))
        self.assertNotEqual(normalize('https://example.com/a?x=1'),
                            normalize('https://example.com/a?x=2'))

    def test_scheme_matters(self):
        self.assertNotEqual(normalize('http://example.com/a'),
                            normalize('https://example.com/a'))


class GuessTypeTest(unittest.TestCase):
    def test_extensions(self):
        cases = {
            'https://example.com/a.css?v=1': 'css',
            'https://example.com/a.js': 'js',
            'https://example.com/a.woff2': 'font',
            'https://example.com/a.avif': 'img',
            'https://example.com/favicon.ico': 'icon',
            'https://example.com/a.mp4': 'video',
            'https://example.com/noext': 'other',
        }
        for url, expected in cases.items():
            self.assertEqual(guess_type(url), expected, url)


class HostOfTest(unittest.TestCase):
    def test_host(self):
        self.assertEqual(host_of('https://CDN.example.net:8443/x'), 'cdn.example.net')

    def test_empty(self):
        self.assertEqual(host_of('not a url'), '')


class DecodeBodyTest(unittest.TestCase):
    def test_utf8_default(self):
        self.assertEqual(decode_body('привет'.encode()), 'привет')

    def test_bom(self):
        self.assertEqual(decode_body(b'\xef\xbb\xbfhi'), 'hi')

    def test_content_type_charset(self):
        body = 'привет'.encode('cp1251')
        self.assertEqual(decode_body(body, 'text/html; charset=windows-1251'), 'привет')

    def test_meta_charset(self):
        body = ('<meta charset="windows-1251">привет').encode('cp1251')
        self.assertIn('привет', decode_body(body, 'text/html'))

    def test_broken_bytes_do_not_raise(self):
        text = decode_body(b'\xff\xfe\xff', 'text/html')
        self.assertIsInstance(text, str)
