"""Unit-тесты детекта антибот-защиты (webcheck/bot.py)."""

import unittest

from webcheck import bot, i18n
from webcheck.checks import run_checks
from webcheck.fetch import FetchResult
from webcheck.report import build_report


def _result(body='', status=200, cookies=None, content_type='text/html'):
    result = FetchResult('https://example.com/', 'page')
    result.status = status
    result.content_type = content_type
    result.body = body.encode('utf-8') if isinstance(body, str) else body
    if cookies:
        result.headers = {'set-cookie': [cookies]}
    return result


class DetectTest(unittest.TestCase):
    def test_js_challenge_cookie(self):
        info = bot.detect(_result(
            '<html><script>document.cookie="x=1";'
            'window.location.href="/";</script></html>',
            cookies='__js_p_=1; Path=/'))
        self.assertIsNotNone(info)
        self.assertEqual(info['level'], 'high')
        self.assertIn('challenge-cookie', info['signals'])

    def test_cloudflare_like(self):
        info = bot.detect(_result(
            '<html><title>Just a moment...</title>'
            '<script src="/cdn-cgi/challenge-platform/h/b/orchestrate/jsch/v1"></script>'
            '</html>'))
        self.assertIsNotNone(info)
        self.assertEqual(info['level'], 'high')

    def test_status_with_js_redirect(self):
        info = bot.detect(_result(
            '<html><script>location.href="/check";</script></html>',
            status=403))
        self.assertIsNotNone(info)
        self.assertEqual(info['level'], 'high')

    def test_possible_browser_check(self):
        info = bot.detect(_result(
            '<html><script>document.cookie="a=1";window.location.href="/";'
            '</script></html>'))
        self.assertIsNotNone(info)
        self.assertEqual(info['level'], 'possible')

    def test_normal_page(self):
        self.assertIsNone(bot.detect(_result(
            '<html><head><link rel="stylesheet" href="/a.css"></head>'
            '<body><h1>Hello</h1><script src="/app.js"></script></body></html>')))

    def test_captcha_word_alone_is_not_enough(self):
        self.assertIsNone(bot.detect(_result(
            '<html><body><p>How CAPTCHA works</p></body></html>')))

    def test_captcha_with_challenge_status(self):
        info = bot.detect(_result(
            '<html><script src="/recaptcha.js"></script></html>', status=403))
        self.assertIsNotNone(info)
        self.assertEqual(info['level'], 'high')

    def test_js_redirect_only_is_not_enough(self):
        self.assertIsNone(bot.detect(_result(
            '<html><script>window.location.href="/next";</script></html>')))


class IntegrationTest(unittest.TestCase):
    def _page(self, level='high'):
        return {
            'url': 'https://example.com/', 'final_url': 'https://example.com/',
            'status': 200, 'http_version': '2', 'content_type': 'text/html',
            'size': 100, 'timings_ms': {}, 'redirects': [], 'headers': {},
            'error': None,
            'bot_protection': {'level': level, 'signals': ['challenge-cookie']},
        }

    def test_checks_warn_and_explain_empty_assets(self):
        messages = ' | '.join(c['message'] for c in run_checks(self._page(), []))
        self.assertIn('антибот', messages)
        self.assertIn('антибот-заглушка', messages)

    def test_report_has_protection_line(self):
        saved = i18n.get_lang()
        try:
            i18n.set_lang('ru')
            text = build_report('https://example.com/', {'page': self._page()})
        finally:
            i18n.set_lang(saved)
        self.assertIn('антибот-защита', text)
        self.assertNotIn('example.com', text.split('защита:')[1].splitlines()[0])

    def test_english_report(self):
        saved = i18n.get_lang()
        try:
            i18n.set_lang('en')
            text = build_report('https://example.com/', {'page': self._page()})
        finally:
            i18n.set_lang(saved)
        self.assertIn('anti-bot protection', text)


if __name__ == '__main__':
    unittest.main()
