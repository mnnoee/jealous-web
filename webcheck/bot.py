import re

from .urls import decode_body

BOT_COOKIE_MARKERS = (
    '__js_p_', '__jhash_', '__jua_', '__cf_bm', 'cf_clearance', '__cf_chl',
    'ddos-guard', 'qrator', 'incap_ses', 'visid_incap', 'sucuri_cloudproxy',
    'aws-waf-token', '_px', 'px_', 'smartcaptcha', 'captcha',
)

BOT_STRONG_MARKERS = (
    'cf_chl', 'cf-chl', 'challenge-platform', 'cdn-cgi/challenge-platform',
    'ddos-guard', 'ddosguard', 'qrator', 'variti', 'incapsula', 'imperva',
    'sucuri', 'awswaf', 'js-challenge', 'jschallenge', 'bot-protection',
    'antibot', 'anti-bot', 'checking your browser', 'just a moment',
    'enable javascript and cookies', 'ddos protection', 'attention required',
    'verify you are human', 'проверка браузера', 'подтвердите, что вы не робот',
)

BOT_SOFT_MARKERS = (
    'captcha', 'recaptcha', 'hcaptcha', 'turnstile', 'smartcaptcha',
)

JS_REDIRECT_MARKERS = (
    'window.location.href', 'location.href', 'document.location',
    'location.replace',
)

META_REFRESH_RE = re.compile(r'<meta[^>]+http-equiv=["\']?refresh', re.I)
SMALL_PAGE_BYTES = 64 * 1024
CHALLENGE_STATUSES = (401, 403, 406, 418, 429, 503)


def _header_values(headers, name):
    return ' '.join((headers or {}).get(name) or []).lower()


def detect(result):

    body = getattr(result, 'body', None)
    if not body:
        return None
    text = decode_body(body, getattr(result, 'content_type', ''))
    if not text:
        return None
    low = text.lower()
    headers = getattr(result, 'headers', None) or {}
    cookies = _header_values(headers, 'set-cookie')

    signals = []
    if any(marker in cookies for marker in BOT_COOKIE_MARKERS):
        signals.append('challenge-cookie')
    if any(marker in low for marker in BOT_STRONG_MARKERS):
        signals.append('challenge-script')
    if any(marker in low for marker in BOT_SOFT_MARKERS):
        signals.append('captcha-widget')
    js_redirect = any(marker in low for marker in JS_REDIRECT_MARKERS)
    js_cookie = 'document.cookie' in low
    if js_redirect:
        signals.append('js-redirect')
    if js_cookie:
        signals.append('js-cookie')
    if META_REFRESH_RE.search(low):
        signals.append('meta-refresh')

    status = getattr(result, 'status', None) or 0
    small = len(body) <= SMALL_PAGE_BYTES
    if status in CHALLENGE_STATUSES:
        signals.append('http-status')
    if small:
        signals.append('small-page')

    if 'challenge-cookie' in signals or 'challenge-script' in signals:
        return {'level': 'high', 'signals': signals}
    if status in CHALLENGE_STATUSES and (
            js_redirect or js_cookie or small or 'captcha-widget' in signals):
        return {'level': 'high', 'signals': signals}

    if small and js_redirect and js_cookie:
        return {'level': 'possible', 'signals': signals}
    if small and js_redirect and 'meta-refresh' in signals:
        return {'level': 'possible', 'signals': signals}
    return None
