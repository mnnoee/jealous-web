"""Загрузка одного URL через curl и разбор его телеметрии.

Почему curl, а не urllib: нужны фазы запроса (DNS/TCP/TLS/TTFB), версия
HTTP и поведение редиректов - ровно то, что печатает `curl -w`. Это тот же
подход, что `dig`/`openssl` в остальных модулях: внешняя утилита, тонкая
обёртка, никаких зависимостей Python.
"""

import json
import os
import re
import subprocess
import tempfile
from urllib.parse import urlparse

from .constants import DEFAULT_TIMEOUT, MAX_BODY_BYTES, MAX_REDIRECTS, USER_AGENT

# JSON, который curl печатает в stdout после запроса.
CURL_FORMAT = """{
"time_namelookup": %{time_namelookup},
"time_connect": %{time_connect},
"time_appconnect": %{time_appconnect},
"time_pretransfer": %{time_pretransfer},
"time_redirect": %{time_redirect},
"time_starttransfer": %{time_starttransfer},
"time_total": %{time_total},
"num_redirects": %{num_redirects},
"http_version": "%{http_version}",
"http_code": %{http_code},
"size_download": %{size_download},
"size_header": %{size_header},
"url_effective": "%{url_effective}",
"scheme": "%{scheme}",
"remote_ip": "%{remote_ip}",
"remote_port": "%{remote_port}",
"content_type": "%{content_type}"
}"""

_STATUS_RE = re.compile(r'^HTTP/[\d.]+\s+(\d{3})')
_HTML_TYPES = ('text/html', 'application/xhtml')
_TEXT_KEEP_EXT = ('.css', '.html', '.htm')


class FetchResult:
    """Результат одного запроса; поля заполняются по мере разбора."""

    __slots__ = (
        'url', 'final_url', 'status', 'http_version', 'size', 'timings',
        'content_type', 'body', 'rtype', 'error', 'headers', 'redirects',
        'scheme', 'remote_ip', 'remote_port', 'num_redirects',
    )

    def __init__(self, url, rtype=None):
        self.url = url
        self.final_url = url
        self.status = None
        self.http_version = None
        self.size = 0
        self.timings = {}
        self.content_type = ''
        self.body = None
        self.rtype = rtype
        self.error = None
        self.headers = {}
        self.redirects = []
        self.scheme = urlparse(url).scheme
        self.remote_ip = ''
        self.remote_port = ''
        self.num_redirects = 0


def _parse_block(lines):
    """Один блок заголовков -> (status, {name: [values]}) или None."""
    if not lines:
        return None
    match = _STATUS_RE.match(lines[0])
    if not match:
        return None
    status = int(match.group(1))
    if 100 <= status < 200:  # промежуточные ответы не нужны
        return None

    headers = {}
    last_name = None
    for line in lines[1:]:
        if line[:1] in (' ', '\t') and last_name:
            # obs-fold: продолжение предыдущего заголовка
            headers[last_name][-1] += ' ' + line.strip()
            continue
        if ':' not in line:
            continue
        name, _, value = line.partition(':')
        last_name = name.strip().lower()
        headers.setdefault(last_name, []).append(value.strip())
    return status, headers


def parse_header_blocks(text):
    """Все ответы из `curl -D`: редиректы и финальный.

    Возвращает [(status, headers), ...] в порядке получения.
    """
    blocks = []
    current = []
    for raw in text.splitlines():
        line = raw.rstrip('\r')
        if not line:
            block = _parse_block(current)
            if block is not None:
                blocks.append(block)
            current = []
            continue
        current.append(line)
    block = _parse_block(current)
    if block is not None:
        blocks.append(block)
    return blocks


def parse_curl_output(text):
    """stdout curl -w -> dict (или None, если это не JSON)."""
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None
    return data if isinstance(data, dict) else None


def _read_headers(path):
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            return f.read()
    except OSError:
        return ''


def _keep_body(res):
    """Тело нужно только для HTML/CSS: по нему ищем ресурсы и @import."""
    content_type = (res.content_type or '').lower()
    if any(t in content_type for t in _HTML_TYPES) or 'css' in content_type:
        return True
    path = res.url.lower().split('?')[0]
    return path.endswith(_TEXT_KEEP_EXT)


def fetch(url, timeout=DEFAULT_TIMEOUT, http2=True, insecure=False,
          compress=True, user_agent=USER_AGENT, rtype=None):
    """Скачать URL, вернуть FetchResult. Никогда не бросает сетевые ошибки."""
    res = FetchResult(url, rtype)

    body_fd, body_path = tempfile.mkstemp(prefix='jealous-web-body-')
    header_fd, header_path = tempfile.mkstemp(prefix='jealous-web-headers-')
    os.close(body_fd)
    os.close(header_fd)

    try:
        env = os.environ.copy()
        env['LC_ALL'] = 'C'

        cmd = [
            'curl', '-L', '--max-redirs', str(MAX_REDIRECTS),
            '--max-time', f'{timeout:g}',
            '--connect-timeout', f'{min(timeout, 10):g}',
            '--proto', '=http,https',
            '-A', user_agent,
            '-sS', '-D', header_path, '-o', body_path,
            '-w', CURL_FORMAT,
        ]
        if http2:
            cmd.append('--http2')
        if insecure:
            cmd.append('-k')
        if compress:
            cmd.append('--compressed')
        else:
            cmd += ['-H', 'Accept-Encoding: identity']
        cmd.append(url)

        try:
            proc = subprocess.run(
                cmd, capture_output=True, env=env, timeout=timeout + 10)
        except FileNotFoundError:
            res.error = 'curl not found in PATH'
            return res
        except subprocess.TimeoutExpired:
            res.error = f'curl timeout after {timeout:g}s'
            return res

        if proc.returncode != 0:
            stderr = proc.stderr.decode('utf-8', 'replace').strip()
            # Берём последнюю строку: первая часто эхо опций/прогресса.
            res.error = stderr.splitlines()[-1] if stderr else f'curl exit {proc.returncode}'
            return res

        data = parse_curl_output(proc.stdout.decode('utf-8', 'replace'))
        if data is None:
            res.error = 'cannot parse curl output (expected JSON)'
            return res

        res.status = int(data.get('http_code') or 0)
        res.http_version = data.get('http_version') or None
        res.final_url = data.get('url_effective') or url
        res.scheme = data.get('scheme') or urlparse(res.final_url).scheme
        res.size = int(data.get('size_download') or 0)
        res.remote_ip = data.get('remote_ip') or ''
        res.remote_port = data.get('remote_port') or ''
        res.num_redirects = int(data.get('num_redirects') or 0)
        res.content_type = (data.get('content_type') or '').lower()
        for key in ('time_namelookup', 'time_connect', 'time_appconnect',
                    'time_pretransfer', 'time_redirect',
                    'time_starttransfer', 'time_total'):
            res.timings[key] = float(data.get(key) or 0.0)

        blocks = parse_header_blocks(_read_headers(header_path))
        if blocks:
            res.headers = blocks[-1][1]
            if not res.content_type:
                values = res.headers.get('content-type') or ['']
                res.content_type = values[0].lower()
            res.redirects = [
                {'status': status,
                 'location': (headers.get('location') or [''])[0]}
                for status, headers in blocks[:-1]
                if 300 <= status < 400 and headers.get('location')
            ]

        if _keep_body(res):
            try:
                if os.path.getsize(body_path) <= MAX_BODY_BYTES:
                    with open(body_path, 'rb') as f:
                        res.body = f.read()
            except OSError:
                pass

        return res
    finally:
        for path in (body_path, header_path):
            try:
                os.remove(path)
            except OSError:
                pass
