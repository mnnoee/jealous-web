"""Константы: версия, дефолты, пороги."""

VERSION = '0.1.1'

# Источник истины версии - constants.VERSION: pyproject.toml читает её через
# [tool.setuptools.dynamic], __init__.py реэкспортирует как __version__.

DEFAULT_WORKERS = 10
DEFAULT_TIMEOUT = 20.0
DEFAULT_CSS_DEPTH = 3
DEFAULT_TOP = 10

MAX_BODY_BYTES = 5 * 1024 * 1024
MAX_REDIRECTS = 5

USER_AGENT = f'jealous-web/{VERSION} (+https://github.com/mnnoee/jealous-web)'

# Пороги эвристик: это повод проверить, а не приговор.
SLOW_TTFB_MS = 600
HEAVY_PAGE_BYTES = 2 * 1024 * 1024
BIG_ASSET_BYTES = 500 * 1024
HSTS_MIN_MAX_AGE = 15552000  # 180 дней

# Типы, для которых имеет смысл проверять кэширование.
STATIC_TYPES = ('css', 'js', 'img', 'font', 'icon', 'video', 'audio', 'source')

# Значения --filter; всё остальное (preload-*, json, xml, iframe) тоже можно
# фильтровать, просто оно не попадает в короткий список подсказки.
FILTER_TYPES = (
    'css', 'js', 'img', 'font', 'icon', 'video', 'audio',
    'source', 'manifest', 'iframe', 'json', 'xml',
)

# Схемы, которые не качаем и не считаем ресурсами страницы.
SKIP_SCHEMES = (
    'javascript:', 'mailto:', 'tel:', 'data:', 'blob:',
    'about:', 'chrome:', 'moz-extension:',
)
