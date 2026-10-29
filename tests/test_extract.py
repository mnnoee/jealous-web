"""Unit-тесты: извлечение ресурсов из HTML и CSS."""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from webcheck.extract import ResourceExtractor, extract_css_refs, srcset_urls


def _parse(html):
    parser = ResourceExtractor()
    parser.feed(html)
    return parser


class HtmlExtractorTest(unittest.TestCase):
    def test_script_and_stylesheet(self):
        parser = _parse(
            '<script src="/app.js"></script>'
            '<link rel="stylesheet" href="/site.css">')
        self.assertEqual(parser.resources, [
            ('/app.js', 'js'), ('/site.css', 'css')])

    def test_preload_maps_as_to_type(self):
        parser = _parse(
            '<link rel="preload" as="font" href="/f.woff2">'
            '<link rel="preload" as="script" href="/a.js">'
            '<link rel="preload" as="style" href="/a.css">'
            '<link rel="preload" as="fetch" href="/api.json">'
            '<link rel="preload" href="/misc.bin">')
        self.assertEqual([kind for _, kind in parser.resources],
                         ['font', 'js', 'css', 'fetch', 'preload-other'])

    def test_modulepreload_is_js(self):
        parser = _parse('<link rel="modulepreload" href="/m.js">')
        self.assertEqual(parser.resources, [('/m.js', 'js')])

    def test_icons_and_manifest(self):
        parser = _parse(
            '<link rel="icon" href="/favicon.ico">'
            '<link rel="apple-touch-icon" href="/touch.png">'
            '<link rel="manifest" href="/site.webmanifest">')
        self.assertEqual([kind for _, kind in parser.resources],
                         ['icon', 'icon', 'manifest'])

    def test_img_src_and_srcset(self):
        parser = _parse(
            '<img src="/a.png" srcset="/a1.png 1x, /a2.png 2x">')
        self.assertEqual(parser.resources, [
            ('/a1.png', 'img'), ('/a2.png', 'img'), ('/a.png', 'img')])

    def test_source_and_video_poster(self):
        parser = _parse(
            '<picture><source srcset="/a.avif 1x"></picture>'
            '<video src="/v.mp4" poster="/p.jpg"></video>')
        self.assertEqual(parser.resources, [
            ('/a.avif', 'source'), ('/v.mp4', 'video'), ('/p.jpg', 'img')])

    def test_iframe_object_embed(self):
        parser = _parse(
            '<iframe src="/frame.html"></iframe>'
            '<object data="/x.swf"></object>'
            '<embed src="/y.pdf">')
        self.assertEqual([kind for _, kind in parser.resources],
                         ['iframe', 'object', 'embed'])

    def test_base_href(self):
        parser = _parse('<base href="https://cdn.example.net/assets/">')
        self.assertEqual(parser.base_href, 'https://cdn.example.net/assets/')

    def test_inline_style_block_and_attribute(self):
        parser = _parse(
            '<style>body { background: url(/bg.png) }</style>'
            '<div style="background-image: url(/attr.png)"></div>')
        self.assertEqual(parser.inline_styles, ['body { background: url(/bg.png) }'])
        self.assertIn('background-image: url(/attr.png)', parser.style_attrs[0])

    def test_srcset_urls(self):
        self.assertEqual(srcset_urls('/a.png 1x, /b.png 2x'),
                         ['/a.png', '/b.png'])
        self.assertEqual(srcset_urls(''), [])


class CssExtractorTest(unittest.TestCase):
    def test_url_quotes_and_bare(self):
        css = ("a{background:url('/a.png')}"
               "b{background:url(\"/b.png\")}"
               "c{background:url(/c.png)}")
        self.assertEqual(extract_css_refs(css), ['/a.png', '/b.png', '/c.png'])

    def test_import_and_url(self):
        css = '@import "base.css"; @import url(theme.css);'
        self.assertEqual(extract_css_refs(css), ['theme.css', 'base.css'])

    def test_comments_removed(self):
        css = '/* url(/hidden.png) */ a{background:url(/shown.png)}'
        self.assertEqual(extract_css_refs(css), ['/shown.png'])

    def test_dedup_preserves_order(self):
        css = 'a{background:url(/a.png)} b{background:url(/a.png)} c{background:url(/b.png)}'
        self.assertEqual(extract_css_refs(css), ['/a.png', '/b.png'])

    def test_empty(self):
        self.assertEqual(extract_css_refs(''), [])
