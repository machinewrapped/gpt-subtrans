# Localization TODO

Authoritative checklist derived from `docs/localization_plan.md`. We will complete items in order and mark them off as they are implemented and validated.

## Phase 1 — Infrastructure Setup

- [X] 1.1 Create localization directory structure and placeholder files
  - Create `locales/`
  - Create `locales/gui-subtrans.pot` (template)
  - Create `locales/en/LC_MESSAGES/gui-subtrans.po`
  - Create `locales/es/LC_MESSAGES/gui-subtrans.po`
  - Add `scripts/extract_strings.py` and `scripts/update_translations.py` (initial stubs)
  - Acceptance: folders and files exist; repository builds unchanged

- [X] 1.2 Add localization module
  - New: `PySubtitle/Helpers/Localization.py` implementing `initialize_localization(language_code=None)`, `_()`, and `tr(context, text)` using `gettext` and `GetResourcePath('locales')`
  - Acceptance: module imports without errors in dev environment

- [X] 1.3 Initialize localization at app startup
  - Update `scripts/gui-subtrans.py` to call `initialize_localization()` before creating the GUI
  - Acceptance: app launches normally (no behavior change yet) when locales missing

- [X] 1.4 Add UI language to settings and settings dialog
  - Add `ui_language` to `PySubtitle/Options.py` defaults and load/save path
  - Add dropdown to `GUI/SettingsDialog.py` under `General` section with languages: `en`, `es` (extendable)
  - Acceptance: value persists via `settings.json`

## Phase 2 — String Extraction and Wrapping

- [X] 2.1 Implement extraction/update scripts
  - `scripts/extract_strings.py`: scan repo for `_()` and `tr()` and generate/update `gui-subtrans.pot`
  - `scripts/update_translations.py`: merge POT into each PO; compile `.mo`
  - Acceptance: running scripts updates POT/PO without errors

- [X] 2.2 Wrap strings in priority UI files
  - `GUI/MainWindow.py`, `GUI/SettingsDialog.py`, `GUI/Widgets/ProjectSettings.py`
  - Use `_()` for strings; `tr()` where context needed
  - Acceptance: English unchanged; keys appear in POT

- [X] 2.3 Wrap remaining GUI strings
  - All dialogs, widgets, menus, commands under `GUI/`
  - Acceptance: 100% of visible strings wrapped
  - Progress: See "Files processed so far" - all major GUI components completed.

- [X] 2.4 Wrap provider/client messages (non-GUI)
  - Strings in `PySubtitle/Providers/` and relevant helpers
  - Acceptance: translatable messages extracted; avoid translating protocol/model IDs
  - Progress: All 8 provider files updated with localization support for GetOptions() strings

## Phase 3 — Translations and First-Run

- [X] 3.1 Seed translations
  - Populate `en` PO from POT; create initial `es` PO with a few sample strings
  - Acceptance: compiled `.mo` loads; Spanish shows for wrapped strings
  - Progress: Best-effort Spanish seeding completed via `scripts/seed_es_translations.py` (many entries auto-filled); remaining empty entries require manual QA.

- [X] 3.2 First-run language selection
  - Update `GUI/FirstRunOptions.py` to include language dropdown; default to system locale
  - Acceptance: selection saved to `ui_language`

## Phase 4 — Testing and Refinement

- [ ] 4.1 Add unit tests for localization
  - Tests for `initialize_localization`, fallback behavior, and runtime switching
  - Acceptance: tests pass locally and in CI

- [ ] 4.2 Manual verification
  - Sanity check UI in `en` and `es`; verify text length and encoding
  - Acceptance: no layout regressions in main views

## Phase 5 — Build/Distribution

- [ ] 5.1 Build scripts
  - Update `scripts/makedistro.sh` and `scripts/makedistro.bat` to compile `.po` → `.mo` and include `locales/`
  - Acceptance: distributions include locale files; app uses them

## Maintenance

- [ ] 6.1 Contributor docs
  - Brief `docs/localization_contributing.md` for translators (workflow, tools, style)
  - Acceptance: linked from `readme.md`

---

Files processed so far (wrapped for i18n and included in POT)
- GUI/AboutDialog.py
- GUI/CommandQueue.py
- GUI/EditInstructionsDialog.py
- GUI/FirstRunOptions.py
- GUI/GuiHelpers.py
- GUI/GuiInterface.py
- GUI/MainToolbar.py
- GUI/MainWindow.py
- GUI/NewProjectSettings.py
- GUI/ProjectActions.py
- GUI/ProjectDataModel.py
- GUI/ProjectToolbar.py
- GUI/SettingsDialog.py
- GUI/ViewModel/BatchItem.py
- GUI/Widgets/Editors.py
- GUI/Widgets/MenuBar.py
- GUI/Widgets/ProjectSettings.py
- GUI/Widgets/ScenesView.py
- GUI/Widgets/Widgets.py

Commands processed (user-facing messages wrapped)
- GUI/Commands/AutoSplitBatchCommand.py
- GUI/Commands/DeleteLinesCommand.py
- GUI/Commands/EditBatchCommand.py
- GUI/Commands/EditLineCommand.py
- GUI/Commands/LoadSubtitleFile.py
- GUI/Commands/MergeLinesCommand.py
- GUI/Commands/MergeScenesCommand.py
- GUI/Commands/ReparseTranslationsCommand.py
- GUI/Commands/SplitBatchCommand.py
- GUI/Commands/SplitSceneCommand.py
- GUI/Commands/StartTranslationCommand.py
- GUI/Commands/TranslateSceneCommand.py
- GUI/GUICommands.py (Exit/CheckProviderSettings)

Providers processed (settings strings wrapped)
- PySubtitle/Providers/Provider_Azure.py
- PySubtitle/Providers/Provider_Bedrock.py  
- PySubtitle/Providers/Provider_Claude.py
- PySubtitle/Providers/Provider_Custom.py
- PySubtitle/Providers/Provider_DeepSeek.py
- PySubtitle/Providers/Provider_Gemini.py
- PySubtitle/Providers/Provider_Mistral.py
- PySubtitle/Providers/Provider_OpenAI.py

Settings dialog localization fixes
- GUI/Widgets/OptionsWidgets.py - Modified GenerateName() to use _() instead of programmatic generation
- SettingsDialog now properly localizes all setting names and descriptions including dynamic provider settings

Scripts and tools developed
- scripts/extract_strings.py - Enhanced with provider settings extraction (static + dynamic analysis)
- scripts/update_translations.py - Moved from locales/ directory, uses proper base_path pattern
- scripts/seed_es_translations.py - Moved from locales/ directory, auto-generates Spanish translations
- scripts/update_providers_localization.py - Batch script to add localization to all providers

Current status: 368 translatable strings extracted (up from 330), including comprehensive provider settings coverage.

Notes
- Use `gettext` stdlib; avoid extra runtime deps
- Start with `en` and `es`; add more languages after coverage is stable
- Prefer `_()` for general strings and `tr(context, text)` where disambiguation is needed


