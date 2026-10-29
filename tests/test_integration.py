"""Интеграционные тесты: живая сеть (по умолчанию отключены).

Запуск: pytest -m integration
"""

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from webcheck import core


@pytest.mark.integration
def test_example_com_page():
    sections, checks, elapsed = core.run(
        'https://example.com/', run_sections=('page',), timeout=15)
    page = sections['page']
    assert page['error'] is None, page['error']
    assert 200 <= page['status'] < 400
    assert page['timings_ms']['total'] >= 0
    assert isinstance(checks, list)
    assert elapsed > 0


@pytest.mark.integration
def test_example_com_assets():
    sections, _, _ = core.run('https://example.com/', timeout=15)
    assert sections['assets']['error'] is None
    assert isinstance(sections['assets']['items'], list)
