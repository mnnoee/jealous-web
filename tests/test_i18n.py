"""Unit-тесты локализации (webcheck/i18n.py)."""

import unittest

from webcheck import i18n
from webcheck.i18n import detect_lang, get_lang, lang_from_locale, set_lang, t


class LocaleDetectTest(unittest.TestCase):
    def test_lc_all_c_is_english(self):
        self.assertEqual(detect_lang({"LC_ALL": "C"}), "en")

    def test_lc_all_ru_is_russian(self):
        self.assertEqual(detect_lang({"LC_ALL": "ru_RU"}), "ru")
        self.assertEqual(detect_lang({"LC_ALL": "ru_RU.UTF-8"}), "ru")

    def test_english_locale(self):
        self.assertEqual(detect_lang({"LANG": "en_US.UTF-8"}), "en")

    def test_posix_and_c_utf8_are_english(self):
        self.assertEqual(detect_lang({"LC_ALL": "POSIX"}), "en")
        self.assertEqual(detect_lang({"LANG": "C.UTF-8"}), "en")

    def test_lc_all_wins_over_lang(self):
        self.assertEqual(detect_lang({"LC_ALL": "C", "LANG": "ru_RU.UTF-8"}), "en")
        self.assertEqual(detect_lang({"LC_ALL": "ru_RU.UTF-8", "LANG": "en_US.UTF-8"}), "ru")

    def test_empty_lc_all_falls_through(self):
        self.assertEqual(detect_lang({"LC_ALL": "", "LC_MESSAGES": "", "LANG": "ru_RU.UTF-8"}), "ru")

    def test_no_locale_defaults_to_english(self):
        self.assertEqual(detect_lang({}), "en")

    def test_unknown_locale_defaults_to_english(self):
        self.assertEqual(detect_lang({"LANG": "de_DE.UTF-8"}), "en")

    def test_language_list(self):
        self.assertEqual(lang_from_locale("ru_RU:en_US"), "ru")
        self.assertEqual(lang_from_locale("en_US:ru_RU"), "en")


class TranslateTest(unittest.TestCase):
    def setUp(self):
        self._saved = get_lang()

    def tearDown(self):
        set_lang(self._saved)

    def test_russian(self):
        set_lang("ru")
        self.assertEqual(t("rep.page"), "--- Страница ---")
        self.assertEqual(t("chk.status", status=404), "страница отвечает статусом 404")

    def test_english(self):
        set_lang("en")
        self.assertEqual(t("rep.page"), "--- Page ---")
        self.assertEqual(t("chk.status", status=404), "the page responds with status 404")

    def test_kwargs_do_not_conflict(self):
        set_lang("ru")
        self.assertIn("10 ms", t("chk.slow_ttfb", ttfb=10, limit=600))
        self.assertIn("example.com", t("chk.assets_failed", n=1, url="https://example.com/"))

    def test_all_catalogs_have_same_keys(self):
        self.assertEqual(set(i18n._CATALOG["ru"]), set(i18n._CATALOG["en"]))

    def test_english_catalog_has_no_cyrillic(self):
        import re
        for msg_id, value in i18n._CATALOG["en"].items():
            self.assertIsNone(re.search(r"[А-Яа-яЁё]", value), msg=msg_id)

    def test_no_em_dash_in_catalogs(self):
        for lang, catalog in i18n._CATALOG.items():
            for msg_id, value in catalog.items():
                self.assertNotIn("\u2014", value, msg=msg_id + ":" + lang)

    def test_unknown_key_falls_back_to_itself(self):
        set_lang("en")
        self.assertEqual(t("no.such.key"), "no.such.key")


if __name__ == "__main__":
    unittest.main()
