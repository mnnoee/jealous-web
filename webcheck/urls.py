"""URL-утилиты: абсолютные ссылки, ключ дедупликации, тип по расширению.

Здесь нет сети: чистые функции, которые легко тестировать.
"""

import codecs
import re
from urllib.parse import urldefrag, urljoin, urlparse, urlunparse

from .constants import SKIP_SCHEMES

_CHARSET_RE = re.compile(r'charset\s*=\s*["\']?([\w.:-]+)', re.I)
_META_CHARSET_RE = re.compile(
    rb'<meta[^>]+charset\s*=\s*["\']?([\w.:-]+)', re.I)
_SCHEME_RE = re.compile(r'^[a-z][a-z0-9+.-]*://', re.I)

_TYPE_BY_EXT = {
    '.css': 'css',
    '.js': 'js',
    '.mjs': 'js',
    '.json': 'json',
    '.xml': 'xml',
    '.png': 'img',
    '.jpg': 'img',
    '.jpeg': 'img',
    '.gif': 'img',
    '.webp': 'img',
    '.avif': 'img',
    '.svg': 'img',
    '.bmp': 'img',
    '.ico': 'icon',
    '.woff': 'font',
    '.woff2': 'font',
    '.ttf': 'font',
    '.otf': 'font',
    '.eot': 'font',
    '.mp4': 'video',
    '.webm': 'video',
    '.ogv': 'video',
    '.mp3': 'audio',
    '.ogg': 'audio',
    '.wav': 'audio',
    '.pdf': 'pdf',
    '.zip': 'archive',
}


def prepare_url(value):
    """Аргумент командной строки -> URL, пригодный для curl.

    - без схемы добавляем https:// (чтобы `jealous-web example.com` работало);
    - не-ASCII хост переводим в punycode: curl не всегда собран с IDN,
      а `смешнявки.рф` иначе может уйти в сеть как есть.
    """
    value = (value or '').strip()
    if not value:
        return value
    if not _SCHEME_RE.match(value):
        value = 'https://' + value

    parsed = urlparse(value)
    host = parsed.hostname or ''
    if not host:
        return value
    try:
        ascii_host = host.encode('idna').decode('ascii')
    except UnicodeError:
        ascii_host = host
    if ascii_host == host:
        return value

    userinfo = ''
    if parsed.username:
        userinfo = parsed.username
        if parsed.password:
            userinfo += ':' + parsed.password
        userinfo += '@'
    try:
        port = f':{parsed.port}' if parsed.port else ''
    except ValueError:
        port = ''
    netloc = f'{userinfo}{ascii_host}{port}'
    return urlunparse(parsed._replace(netloc=netloc))


def make_absolute(base, href):
    """Ссылка из HTML/CSS -> абсолютный http(s) URL без фрагмента.

    Возвращает None для пустых, служебных (mailto:, data:, javascript:)
    и любых не-http схем.
    """
    if not href:
        return None
    href = href.strip()
    if not href:
        return None
    if href.lower().startswith(SKIP_SCHEMES):
        return None
    try:
        absolute = urljoin(base, href)
    except ValueError:
        return None
    if not absolute.lower().startswith(('http://', 'https://')):
        return None
    absolute, _ = urldefrag(absolute)
    return absolute


def normalize(url):
    """Ключ дедупликации: схема, хост, путь, query (фрагмент уже отброшен)."""
    p = urlparse(url)
    path = p.path or '/'
    if len(path) > 1 and path.endswith('/'):
        path = path.rstrip('/')
    return (p.scheme, p.netloc.lower(), path, p.query)


def host_of(url):
    """Хост без порта в нижнем регистре (для сравнения «свой/сторонний»)."""
    try:
        return (urlparse(url).hostname or '').lower()
    except ValueError:
        return ''


def guess_type(url):
    """Тип ресурса по расширению пути; 'other', если не угадали."""
    path = urlparse(url).path.lower()
    dot = path.rfind('.')
    if dot == -1:
        return 'other'
    return _TYPE_BY_EXT.get(path[dot:], 'other')


def decode_body(body, content_type=''):
    """Байты -> текст: BOM, charset из заголовка, <meta charset>, utf-8.

    Без этого страницы в windows-1251/koi8-r дают битые ссылки: HTML
    разбирается, но URL в нём уже испорчены.
    """
    if not body:
        return ''
    if body.startswith(codecs.BOM_UTF8):
        return body.decode('utf-8-sig', 'replace')

    encodings = []
    match = _CHARSET_RE.search(content_type or '')
    if match:
        encodings.append(match.group(1))
    head = body[:4096]
    meta = _META_CHARSET_RE.search(head)
    if meta:
        encodings.append(meta.group(1).decode('ascii', 'ignore'))
    encodings.append('utf-8')

    for encoding in encodings:
        if not encoding:
            continue
        try:
            return body.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            continue
    return body.decode('utf-8', 'replace')
