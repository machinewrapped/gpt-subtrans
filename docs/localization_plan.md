# GPT-SubTrans Localization Plan

## Overview

This document outlines a comprehensive plan for adding internationalization (i18n) and localization (l10n) support to the GPT-SubTrans application, enabling users to select their preferred UI language during installation or first run.

## Current State Analysis

### Codebase Structure
- **GUI Framework**: PySide6 (Qt for Python)
- **Architecture**: Desktop application with PyQt-based GUI
- **Main Components**:
  - Main window with toolbar and splitter layout
  - Settings dialog with tabbed interface
  - About dialog with version information
  - Menu bar with File/Edit/Tools menus
  - Various widgets and dialogs

### Current String Management
- All UI strings are currently hardcoded in English within Python files
- No existing localization infrastructure found
- Settings system exists but no language preference setting

## Recommended Approach

### 1. Localization Library Selection

**Recommended**: Use Qt's built-in internationalization system with Python's `gettext` module as a fallback for non-Qt strings.

**Primary Solution - Qt Linguist Workflow**:
- **Library**: Qt's built-in i18n system (QTranslator, QApplication.translate())
- **License**: LGPL/Commercial (compatible with MIT)
- **Tools**: Qt Linguist for translation management
- **File Format**: `.ts` (translation source) and `.qm` (compiled translation)

**Secondary Solution - Python gettext**:
- **Library**: Python's built-in `gettext` module
- **License**: Python Software Foundation License (MIT-compatible)
- **File Format**: `.po`/.pot files
- **Tools**: Standard gettext tools, Poedit, or web-based translation tools

### 2. Implementation Strategy

#### Phase 1: Infrastructure Setup
1. **Create localization directory structure**:
   ```
   locales/
   ├── en/
   │   └── LC_MESSAGES/
   │       ├── gui-subtrans.pot (template)
   │       └── gui-subtrans.po
   ├── es/
   │   └── LC_MESSAGES/
   │       └── gui-subtrans.po
   ├── fr/
   │   └── LC_MESSAGES/
   │       └── gui-subtrans.po
   └── de/
       └── LC_MESSAGES/
           └── gui-subtrans.po
   ```

2. **Add language preference to settings**:
   - Add `ui_language` option to `PySubtitle/Options.py`
   - Update `GUI/SettingsDialog.py` to include language selection dropdown
   - Store preference in user settings file

3. **Create translation initialization module**:
   - New file: `PySubtitle/Helpers/Localization.py`
   - Handle language detection and translator setup
   - Provide translation function (`_()` or `tr()`)

#### Phase 2: String Extraction and Wrapping
1. **Create string extraction script**:
   - Script to scan Python files for translatable strings
   - Generate `.pot` template file
   - Update existing `.po` files

2. **Wrap UI strings systematically**:
   - Start with main dialogs and menus
   - Progress through all GUI components
   - Use consistent translation function calls

3. **Handle dynamic strings**:
   - Error messages
   - Status messages
   - Provider-specific strings

#### Phase 3: Translation Management
1. **Set up translation workflow**:
   - Create initial translations for key languages (Spanish, French, German, Chinese)
   - Establish process for translator contributions
   - Set up validation and testing procedures

2. **Add first-run language selection**:
   - Modify `GUI/FirstRunOptions.py` to include language selection
   - Auto-detect system locale as default
   - Store selection for future use

#### Phase 4: Testing and Refinement
1. **Test language switching**:
   - Runtime language switching capability
   - Verify all strings are properly translated
   - Test with different text lengths and character sets

2. **Handle special cases**:
   - Right-to-left languages (Arabic, Hebrew)
   - Font requirements for different scripts
   - Date/time formatting
   - Number formatting

### 3. Technical Implementation Details

#### Translation Function Integration
```python
# PySubtitle/Helpers/Localization.py
import gettext
import os
from PySubtitle.Options import Options

_translator = None

def initialize_localization(language_code=None):
    global _translator
    if language_code is None:
        options = Options()
        language_code = options.get('ui_language', 'en')
    
    locale_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'locales')
    try:
        _translator = gettext.translation('gui-subtrans', locale_dir, [language_code])
        _translator.install()
    except FileNotFoundError:
        # Fallback to English
        _translator = gettext.NullTranslations()
        _translator.install()

def _(text):
    """Get translated string"""
    if _translator:
        return _translator.gettext(text)
    return text

def tr(context, text):
    """Get translated string with context"""
    if _translator:
        return _translator.pgettext(context, text)  
    return text
```

#### Settings Integration
```python
# Add to GUI/SettingsDialog.py SECTIONS
'Interface': {
    'ui_language': ([], "Interface language"),
    # ... other interface settings
}
```

#### Main Application Integration
```python
# Modify scripts/gui-subtrans.py
from PySubtitle.Helpers.Localization import initialize_localization

def main():
    # ... existing code ...
    
    # Initialize localization before creating GUI
    initialize_localization()
    
    # ... rest of application startup ...
```

### 4. Supported Languages (Initial Release)

**Priority 1** (Large user bases):
- English (en) - default
- Spanish (es)
- French (fr)
- German (de)
- Chinese Simplified (zh-CN)
- Japanese (ja)

**Priority 2** (Additional languages):
- Portuguese (pt)
- Russian (ru)
- Italian (it)
- Korean (ko)
- Arabic (ar)

### 5. Directory Structure Changes

```
gpt-subtrans/
├── locales/
│   ├── extract_strings.py          # String extraction script
│   ├── update_translations.py      # Update .po files from .pot
│   ├── gui-subtrans.pot           # Translation template
│   ├── en/
│   │   └── LC_MESSAGES/
│   │       ├── gui-subtrans.po
│   │       └── gui-subtrans.mo    # Compiled translation
│   ├── es/
│   │   └── LC_MESSAGES/
│   │       ├── gui-subtrans.po
│   │       └── gui-subtrans.mo
│   └── [other languages...]
├── PySubtitle/
│   └── Helpers/
│       └── Localization.py         # New localization module
└── [existing structure...]
```

### 6. Build and Distribution Updates

#### Requirements Updates
Add to `requirements.txt`:
- No additional dependencies (using Python stdlib `gettext`)

#### Build Script Updates
- Modify `scripts/makedistro.sh` and `scripts/makedistro.bat` to:
  - Compile `.po` files to `.mo` files
  - Include `locales/` directory in distribution
  - Generate translation statistics

#### Installation Script Updates
- Update install scripts to preserve locale files
- Add language selection during installation (optional)

### 7. Development Workflow

#### For Developers
1. **String Addition Process**:
   ```bash
   # After adding new translatable strings
   python locales/extract_strings.py
   python locales/update_translations.py
   ```

2. **Testing Different Languages**:
   ```bash
   # Set environment variable for testing
   export LANG=es_ES.UTF-8
   python scripts/gui-subtrans.py
   ```

#### For Translators
1. **Translation Process**:
   - Use standard `.po` file editors (Poedit, Lokalize, web tools)
   - Test translations in application
   - Submit via pull requests or translation platform

2. **Translation Guidelines**:
   - Maintain consistent terminology
   - Consider UI space constraints
   - Test with sample subtitle files

### 8. Migration Strategy

#### User Experience
- **Existing Users**: Default to English, show language option in settings
- **New Users**: Language selection in first-run dialog
- **Upgrade Path**: Detect system locale for new language setting

#### Backward Compatibility
- All existing functionality remains unchanged
- English strings serve as fallback
- No breaking changes to file formats or APIs

### 9. Testing Strategy

#### Automated Testing
- Unit tests for localization functions
- Verify all UI strings have translation keys
- Test language switching functionality

#### Manual Testing
- Test each supported language end-to-end
- Verify text fits in UI elements
- Test special characters and encoding
- Validate translation accuracy

#### User Acceptance Testing
- Beta testing with native speakers
- Feedback collection system
- Iterative improvements based on user input

### 10. Maintenance and Updates

#### Translation Updates
- Regular extraction of new strings
- Notification system for translators
- Version control for translation files
- Quality assurance process

#### Community Involvement
- Guidelines for community translators
- Recognition system for contributors
- Documentation for translation process
- Integration with translation platforms (Crowdin, Weblate)

## Implementation Timeline

### Week 1-2: Infrastructure
- Set up localization framework
- Create extraction and build scripts
- Add language preference to settings

### Week 3-4: Core Translation
- Wrap main window and dialog strings
- Implement translation loading
- Create initial English template

### Week 5-6: Complete Coverage
- Wrap all remaining UI strings
- Handle dynamic/generated strings
- Add first-run language selection

### Week 7-8: Initial Translations
- Create translations for Priority 1 languages
- Testing and refinement
- Documentation updates

### Week 9-10: Testing and Polish
- Comprehensive testing across languages
- UI adjustments for different text lengths
- Performance optimization
- Final quality assurance

## Success Metrics

1. **Coverage**: 100% of user-visible strings translatable
2. **Performance**: No noticeable performance impact
3. **Usability**: Language switching works seamlessly
4. **Quality**: Translations are accurate and contextually appropriate
5. **Maintainability**: Easy to add new languages and update translations

## Risks and Mitigation

### Technical Risks
- **Text overflow**: Mitigate with responsive UI design and text truncation
- **Character encoding**: Use UTF-8 throughout, test with various scripts
- **Performance impact**: Profile translation lookups, implement caching if needed

### Process Risks
- **Translation quality**: Establish review process, use native speakers
- **Maintenance burden**: Automate string extraction and update processes
- **Community engagement**: Create clear contribution guidelines and recognition

## Conclusion

This localization plan provides a comprehensive approach to internationalizing GPT-SubTrans while maintaining the application's current functionality and performance. The phased implementation allows for iterative development and testing, ensuring a high-quality multilingual user experience.

The use of standard Python `gettext` infrastructure ensures long-term maintainability and compatibility with existing translation tools and workflows. The proposed directory structure and development processes are designed to scale with the addition of new languages and translators.