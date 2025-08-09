"""
Localization utilities using Python's gettext.

This module initializes a gettext translator based on the UI language from
`PySubtitle.Options` and exposes helper functions for translations.
"""
from __future__ import annotations

import gettext
import os
from typing import Optional

from PySubtitle.Helpers.Resources import GetResourcePath
from PySubtitle.Options import Options


_translator: Optional[gettext.NullTranslations] = None
_domain = 'gui-subtrans'


def _get_locale_dir() -> str:
    # Locale directory is resolved via resource path helper so it works in dev and bundled builds
    return GetResourcePath('locales')


def initialize_localization(language_code: Optional[str] = None) -> None:
    """
    Initialize the gettext translation system.

    - If language_code is None, reads from Options().get('ui_language', 'en')
    - Falls back gracefully to NullTranslations when catalogs are missing
    """
    global _translator

    if language_code is None:
        try:
            options = Options()
            language_code = options.get('ui_language', 'en')
        except Exception:
            language_code = 'en'

    locale_dir = _get_locale_dir()

    try:
        _translator = gettext.translation(_domain, localedir=locale_dir, languages=[language_code])
        _translator.install()  # provides built-in _() as well
    except Exception:
        _translator = gettext.NullTranslations()
        _translator.install()


def set_language(language_code: str) -> None:
    """Switch language at runtime."""
    initialize_localization(language_code)


def _(text: str) -> str:
    """Return translated string for the active language."""
    if _translator:
        return _translator.gettext(text)
    return text


def tr(context: str, text: str) -> str:
    """Return translated string with context (pgettext)."""
    if _translator and hasattr(_translator, 'pgettext'):
        return _translator.pgettext(context, text)
    # Fallback: ignore context if pgettext not available
    return _(text)


