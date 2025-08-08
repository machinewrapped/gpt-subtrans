"""
Simple localization support using gettext
"""
import gettext
import os
import locale
from typing import Optional

# Global translator instance
_translator: Optional[gettext.NullTranslations] = None

def initialize_localization(language_code: Optional[str] = None) -> None:
    """
    Initialize the localization system
    
    Args:
        language_code: Language code like 'es', 'fr', 'de'. If None, tries to detect system locale
    """
    global _translator
    
    if language_code is None:
        try:
            # Try to detect system locale
            system_locale = locale.getdefaultlocale()[0]
            if system_locale:
                language_code = system_locale.split('_')[0]  # Extract language part
            else:
                language_code = 'en'
        except:
            language_code = 'en'
    
    # Get the locale directory path
    locale_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'locales')
    
    try:
        _translator = gettext.translation('gui-subtrans', locale_dir, [language_code], fallback=True)
    except Exception:
        # Fallback to NullTranslations if anything goes wrong
        _translator = gettext.NullTranslations()

def _(text: str) -> str:
    """
    Get translated string
    
    Args:
        text: String to translate
        
    Returns:
        Translated string or original if no translation available
    """
    if _translator:
        return _translator.gettext(text)
    return text

def set_language(language_code: str) -> None:
    """
    Change the current language
    
    Args:
        language_code: New language code to use
    """
    initialize_localization(language_code)

def get_available_languages() -> list[str]:
    """
    Get list of available language codes
    
    Returns:
        List of available language codes
    """
    locale_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'locales')
    languages = ['en']  # English is always available (fallback)
    
    try:
        if os.path.exists(locale_dir):
            for item in os.listdir(locale_dir):
                lang_dir = os.path.join(locale_dir, item)
                if os.path.isdir(lang_dir) and item != 'en':
                    mo_file = os.path.join(lang_dir, 'LC_MESSAGES', 'gui-subtrans.mo')
                    if os.path.exists(mo_file):
                        languages.append(item)
    except Exception:
        pass
    
    return languages

# Language display names
LANGUAGE_NAMES = {
    'en': 'English',
    'es': 'Español',
    'fr': 'Français',
    'de': 'Deutsch',
    'zh': '中文',
    'ja': '日本語'
}

def get_language_display_name(language_code: str) -> str:
    """
    Get display name for a language code
    
    Args:
        language_code: Language code like 'es', 'fr'
        
    Returns:
        Display name for the language
    """
    return LANGUAGE_NAMES.get(language_code, language_code)