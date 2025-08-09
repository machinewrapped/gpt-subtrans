"""
Localization utilities using Python's gettext.

This module initializes a gettext translator based on the UI language from
`PySubtitle.Options` and exposes helper functions for translations.
"""
from __future__ import annotations

import gettext
import os
from typing import Optional, List, Tuple, Dict

from PySubtitle.Helpers.Resources import GetResourcePath
from PySubtitle.Options import Options


_translator: Optional[gettext.NullTranslations] = None
_domain = 'gui-subtrans'

# Human-readable locale names mapping
LOCALE_NAMES: Dict[str, str] = {
    'en': 'English',
    'es': 'Español',
    'cs': 'Čeština',
}


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


def get_available_locales() -> List[str]:
    """
    Scan the locales directory and return a list of available locale codes.
    """
    locales_dir = _get_locale_dir()
    languages = []
    try:
        for name in os.listdir(locales_dir):
            path = os.path.join(locales_dir, name, 'LC_MESSAGES')
            if os.path.isdir(path):
                # Check if there's actually a .po or .mo file in this locale
                po_file = os.path.join(path, f'{_domain}.po')
                mo_file = os.path.join(path, f'{_domain}.mo')
                if os.path.exists(po_file) or os.path.exists(mo_file):
                    languages.append(name)
    except Exception:
        # Fallback to known locales if scanning fails
        languages = ['en', 'es']
    
    return sorted(set(languages)) or ['en']


def get_locale_display_name(locale_code: str) -> str:
    """
    Get the human-readable display name for a locale code.
    Falls back to the locale code if no display name is defined.
    """
    return LOCALE_NAMES.get(locale_code, locale_code)


def get_locales_with_names() -> List[Tuple[str, str]]:
    """
    Get a list of (locale_code, display_name) tuples for all available locales.
    """
    locale_codes = get_available_locales()
    return [(code, get_locale_display_name(code)) for code in locale_codes]


class LocaleDisplayItem:
    """
    A simple class to represent a locale with both code and display name.
    This enables the existing dropdown system to show display names while returning codes.
    """
    def __init__(self, code: str, display_name: str):
        self.code = code
        self.display_name = display_name
        self.name = display_name  # For GetValueName() compatibility
    
    def __str__(self):
        return self.code
    
    def __eq__(self, other):
        if isinstance(other, str):
            return self.code == other
        elif isinstance(other, LocaleDisplayItem):
            return self.code == other.code
        return False


def get_locale_display_items() -> List[LocaleDisplayItem]:
    """
    Get a list of LocaleDisplayItem objects for use in dropdowns.
    """
    locales_with_names = get_locales_with_names()
    return [LocaleDisplayItem(code, name) for code, name in locales_with_names]


