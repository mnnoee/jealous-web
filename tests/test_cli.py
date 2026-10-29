"""Unit-тесты: CLI - флаги, выбор секций, JSON, подготовка URL."""

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from webcheck import cli


class ParserTest(unittest.TestCase):
    def test_defaults(self):
        args = cli.build_parser().parse_args(['example.com'])
        self.assertEqual(args.url, 'example.com')
        self.assertFalse(args.page)
        self.assertFalse(args.assets)
        self.assertEqual(args.workers, 10)
        self.assertEqual(args.timeout, 20.0)
        self.assertEqual(args.css_depth, 3)
        self.assertEqual(args.top, 10)
        self.assertIsNone(args.json)
        self.assertFalse(args.no_http2)

    def test_flags(self):
        args = cli.build_parser().parse_args([
            'example.com', '--page', '--assets', '-j', '4', '-t', '5',
            '--css-depth', '1', '--top', '3', '--filter', 'css,js',
            '--no-http2', '--insecure', '--no-compress',
            '--user-agent', 'UA', '--json', 'out.json', '--diagram',
        ])
        self.assertTrue(args.page)
        self.assertTrue(args.assets)
        self.assertEqual(args.workers, 4)
        self.assertEqual(args.timeout, 5.0)
        self.assertEqual(args.css_depth, 1)
        self.assertEqual(args.top, 3)
        self.assertEqual(args.filter, 'css,js')
        self.assertTrue(args.no_http2)
        self.assertTrue(args.insecure)
        self.assertTrue(args.no_compress)
        self.assertEqual(args.user_agent, 'UA')
        self.assertEqual(args.json, 'out.json')
        self.assertTrue(args.diagram)

    def test_json_default_path(self):
        args = cli.build_parser().parse_args(['example.com', '--json'])
        self.assertEqual(args.json, 'report.json')


class SelectionTest(unittest.TestCase):
    def _args(self, *argv):
        return cli.build_parser().parse_args(['example.com'] + list(argv))

    def test_default_is_all(self):
        self.assertEqual(cli._selected(self._args()), ['page', 'assets'])

    def test_page_only(self):
        self.assertEqual(cli._selected(self._args('--page')), ['page'])

    def test_assets_only(self):
        self.assertEqual(cli._selected(self._args('--assets')), ['assets'])

    def test_all(self):
        self.assertEqual(cli._selected(self._args('--all')), ['page', 'assets'])


class TypeFilterTest(unittest.TestCase):
    def test_empty(self):
        self.assertIsNone(cli._type_filter(''))
        self.assertIsNone(cli._type_filter(' , '))

    def test_normalizes(self):
        self.assertEqual(cli._type_filter('css, JS ,font'),
                         {'css', 'js', 'font'})


class MainTest(unittest.TestCase):
    def _run_main(self, argv, sections=None, checks=None):
        sections = sections or {'page': {'url': 'https://example.com/'}}
        with mock.patch.object(cli.core, 'run',
                               return_value=(sections, checks or [], 0.5)) as run, \
                contextlib.redirect_stdout(io.StringIO()) as out:
            cli.main(argv)
        return run, out.getvalue()

    def test_prepares_url(self):
        run, _ = self._run_main(['example.com'])
        self.assertEqual(run.call_args.args[0], 'https://example.com')

    def test_passes_options(self):
        run, _ = self._run_main([
            'example.com', '--page', '--workers', '3', '--no-http2',
            '--insecure', '--no-compress', '--filter', 'css',
            '--css-depth', '2', '--top', '5',
        ])
        kwargs = run.call_args.kwargs
        self.assertEqual(kwargs['workers'], 3)
        self.assertFalse(kwargs['http2'])
        self.assertTrue(kwargs['insecure'])
        self.assertFalse(kwargs['compress'])
        self.assertEqual(kwargs['type_filter'], {'css'})
        self.assertEqual(kwargs['css_depth'], 2)
        self.assertEqual(kwargs['top'], 5)
        self.assertEqual(kwargs['run_sections'], ['page'])

    def test_prints_report(self):
        _, printed = self._run_main(['example.com'])
        self.assertIn('example.com', printed)

    def test_writes_json(self):
        path = os.path.join(tempfile.mkdtemp(), 'web.json')
        stderr = io.StringIO()
        with mock.patch.object(cli.core, 'run',
                               return_value=({'page': {'url': 'https://example.com/',
                                                       'final_url': 'https://example.com/',
                                                       'status': 200,
                                                       'error': None}},
                                             [], 0.5)), \
                contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(stderr):
            cli.main(['example.com', '--json', path])
        with open(path, encoding='utf-8') as f:
            doc = json.load(f)
        self.assertEqual(doc['meta']['status'], 200)
        self.assertIn('JSON', stderr.getvalue())

    def test_error_still_writes_json(self):
        path = os.path.join(tempfile.mkdtemp(), 'web.json')
        sections = {
            'page': {'url': 'https://example.com/', 'error': 'down'},
            'assets': {'items': [], 'by_type': [], 'slowest': [],
                       'total_size': 0, 'error': 'down'},
        }
        with mock.patch.object(cli.core, 'run',
                               return_value=(sections, [], 0.1)), \
                contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            cli.main(['example.com', '--json', path])
        with open(path, encoding='utf-8') as f:
            doc = json.load(f)
        self.assertEqual(doc['page']['error'], 'down')
        self.assertEqual(doc['meta']['resources_total'], 0)


class VersionTest(unittest.TestCase):
    def test_version(self):
        with self.assertRaises(SystemExit), \
                contextlib.redirect_stdout(io.StringIO()) as out:
            cli.main(['--version'])
        self.assertIn('0.1.0', out.getvalue())
