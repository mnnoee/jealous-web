"""Извлечение ресурсов из HTML и CSS.

Не краулер: берём только то, что реально упомянуто в разметке, и не
исполняем JS. Для SPA это значит «почти ничего» - ограничение честно
описано в README.
"""

import re
from html.parser import HTMLParser

# rel -> тип; для preload тип зависит от as="...".
_PRELOAD_TYPES = {
    'style': 'css',
    'script': 'js',
    'font': 'font',
    'image': 'img',
    'video': 'video',
    'audio': 'audio',
    'fetch': 'fetch',
    'document': 'document',
}

CSS_COMMENT_RE = re.compile(r'/\*.*?\*/', re.S)
CSS_URL_RE = re.compile(
    r"""url\(\s*(?:"([^"]*)"|'([^']*)'|([^)'"\s]+))\s*\)""", re.I)
CSS_IMPORT_RE = re.compile(
    r"""@import\s+(?:url\(\s*(?:"([^"]*)"|'([^']*)'|([^)'"\s]+))\s*\)"""
    r"""|"([^"]*)"|'([^']*)')""", re.I)


def srcset_urls(value):
    """URL из srcset="a.jpg 1x, b.jpg 2x".

    Запятые внутри data:-URL отсекаются раньше (make_absolute), поэтому
    простой split по запятой здесь достаточен.
    """
    urls = []
    if not value:
        return urls
    for part in value.split(','):
        part = part.strip()
        if part:
            urls.append(part.split()[0])
    return urls


class ResourceExtractor(HTMLParser):
    """Собирает ссылки на ресурсы, inline-<style> и атрибуты style=""."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.resources = []       # [(href, rtype)]
        self.inline_styles = []   # содержимое <style>...</style>
        self.style_attrs = []     # значения style="..."
        self.base_href = None
        self._in_style = False
        self._style_buf = []

    def handle_starttag(self, tag, attrs):
        data = {k: (v if v is not None else '') for k, v in attrs}
        tag = tag.lower()

        if tag == 'base' and data.get('href'):
            self.base_href = data['href']
        elif tag == 'script' and data.get('src'):
            self.resources.append((data['src'], 'js'))
        elif tag == 'link':
            self._handle_link(data)
        elif tag == 'img':
            self._add_srcset(data)
            if data.get('src'):
                self.resources.append((data['src'], 'img'))
        elif tag == 'source':
            self._add_srcset(data, 'source')
            if data.get('src'):
                self.resources.append((data['src'], 'source'))
        elif tag in ('video', 'audio', 'track', 'embed'):
            if data.get('src'):
                self.resources.append((data['src'], tag))
            if tag == 'video' and data.get('poster'):
                self.resources.append((data['poster'], 'img'))
        elif tag == 'object':
            if data.get('data'):
                self.resources.append((data['data'], 'object'))
        elif tag == 'iframe':
            if data.get('src'):
                self.resources.append((data['src'], 'iframe'))
        elif tag == 'style':
            self._in_style = True
            self._style_buf = []

        if data.get('style'):
            self.style_attrs.append(data['style'])

    def _handle_link(self, data):
        href = data.get('href')
        if not href:
            return
        rel = (data.get('rel') or '').lower().split()
        if 'stylesheet' in rel:
            self.resources.append((href, 'css'))
        elif 'modulepreload' in rel:
            self.resources.append((href, 'js'))
        elif 'preload' in rel:
            as_ = (data.get('as') or '').lower()
            self.resources.append((href, _PRELOAD_TYPES.get(as_, f'preload-{as_ or "other"}')))
        elif 'icon' in rel or 'apple-touch-icon' in rel:
            self.resources.append((href, 'icon'))
        elif 'manifest' in rel:
            self.resources.append((href, 'manifest'))

    def _add_srcset(self, data, rtype=None):
        for url in srcset_urls(data.get('srcset')):
            self.resources.append((url, rtype or 'img'))

    def handle_endtag(self, tag):
        if tag.lower() == 'style' and self._in_style:
            self._in_style = False
            self.inline_styles.append(''.join(self._style_buf))
            self._style_buf = []

    def handle_data(self, data):
        if self._in_style:
            self._style_buf.append(data)


def extract_css_refs(css_text):
    """url(...) и @import из CSS; порядок сохраняется, дубли убираются."""
    if not css_text:
        return []
    css_text = CSS_COMMENT_RE.sub('', css_text)
    urls = []
    for regex in (CSS_URL_RE, CSS_IMPORT_RE):
        for match in regex.finditer(css_text):
            for group in match.groups():
                if group:
                    urls.append(group)
                    break

    seen = set()
    result = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            result.append(url)
    return result
