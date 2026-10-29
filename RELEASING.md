# Релизы

Процесс выпуска новой версии. Одинаков для всех модулей набора
Jealous Moon (`jealous-nginx`, `jealous-strace`, `jealous-domain`,
`jealous-web`).

## Версионирование

[Semantic Versioning](https://semver.org/lang/ru/): `MAJOR.MINOR.PATCH`.

- **MAJOR** — ломающие изменения: удалён флаг, изменена семантика вывода,
  изменён формат JSON-отчёта
- **MINOR** — новая функциональность без ломки: новая секция отчёта,
  новый флаг, новая консольная команда
- **PATCH** — исправления без изменения интерфейса: баг-фиксы, доки

**Источник истины версии — `VERSION` в `webcheck/constants.py`.**
`pyproject.toml` читает её автоматически через `[tool.setuptools.dynamic]`,
`__init__.py` реэкспортирует как `__version__`. Версию нигде больше
дублировать не нужно.

## Чек-лист релиза

1. Убедиться, что тесты и линтер зелёные:
   ```bash
   python -m pytest
   ruff check .
   ```
2. Обновить `VERSION` в `webcheck/constants.py`
3. Добавить запись в `CHANGELOG.md` (Keep a Changelog):
   - дата релиза
   - секции Added / Changed / Fixed / Removed
   - ссылки сравнения версий внизу файла
4. Закоммитить: `git commit -m "Release vX.Y.Z"`
5. Поставить аннотированный тег:
   ```bash
   git tag -a vX.Y.Z -m "jealous-web X.Y.Z"
   ```
6. Проверить, что пакет собирается:
   ```bash
   pip install .
   jealous-web --version   # должна напечатать новую версию
   ```
7. Запушить вместе с тегом:
   ```bash
   git push origin master --tags
   ```

## Синхронизация модулей

Модули независимы и релизятся по отдельности — синхронизировать версии
не нужно. Но при ломающем изменении общего контракта (формат JSON-отчёта,
CLI-флаги), который использует дашборд Jealous Moon, обновите манифест
`modules/conf/web.yaml` в репозитории дашборда и укажите это в CHANGELOG.
