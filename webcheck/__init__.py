"""Пакет webcheck: проверка страницы и всех её ресурсов (тайминги, размеры)."""

# Версия берётся из constants.VERSION - единственный источник истины.
# pyproject.toml читает её через [tool.setuptools.dynamic].
from .constants import VERSION as __version__

__all__ = ['__version__']
