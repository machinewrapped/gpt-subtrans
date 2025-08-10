#!/usr/bin/env python3
"""
One-stop localization workflow for GPT-SubTrans.

Runs the end-to-end flow:
    1) Extract translatable strings -> locales/gui-subtrans.pot
    2) Merge POT into every locale's PO and compile MO catalogs
    3) Integrate any manual translations from untranslated_msgids_<lang>.txt
    4) Re-compile changed POs
    5) Regenerate untranslated_msgids_<lang>.txt (remaining blanks only)

Also normalizes msgid wrapping inside PO files to single-line form so
seeding/matching works reliably.
"""
import os
import re
import sys
import ast
import subprocess
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

# Add the parent directory to sys.path so we can import PySubtitle modules
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_path)

from PySubtitle.Helpers.Localization import get_available_locales

LOCALES_DIR = os.path.join(base_path, 'locales')
POT_PATH = os.path.join(LOCALES_DIR, 'gui-subtrans.pot')


# --- PO cleaner helpers: collapse wrapped msgid lines into a single line ---
def _is_quoted_line(s: str) -> bool:
    s = s.lstrip()
    return s.startswith('"') and s.rstrip().endswith('"')


def _extract_quoted(s: str) -> str:
    s = s.strip()
    try:
        first = s.index('"')
        last = s.rindex('"')
    except ValueError:
        return s
    return s[first + 1:last]


def clean_po_file(path: str) -> bool:
    """Clean a single PO file in-place. Returns True if file changed."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        return False

    out = []
    i = 0
    changed = False

    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()

        if stripped.startswith('msgid '):
            indent_len = len(line) - len(stripped)
            indent = line[:indent_len]

            if '"' not in stripped:
                out.append(line)
                i += 1
                continue

            first_content = _extract_quoted(stripped)

            j = i + 1
            parts = [first_content]
            while j < len(lines) and _is_quoted_line(lines[j]):
                parts.append(_extract_quoted(lines[j]))
                j += 1

            if len(parts) > 1 or (first_content == '' and j > i + 1):
                combined = ''.join(parts)
                out.append(f"{indent}msgid \"{combined}\"\n")
                changed = True
                i = j
                continue
            else:
                out.append(line)
                i += 1
                continue

        out.append(line)
        i += 1

    if changed:
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(out)
    return changed


def _escape_po(s: str) -> str:
    """Escape a Python string for inclusion inside a PO msgstr quoted string."""
    return s.replace('\\', r'\\').replace('"', r'\"').replace('\n', r'\n')


def ensure_dirs(language_code: str) -> str:
    lang_dir = os.path.join(LOCALES_DIR, language_code, 'LC_MESSAGES')
    os.makedirs(lang_dir, exist_ok=True)
    return lang_dir


def ensure_po(language_code: str) -> str:
    lang_dir = ensure_dirs(language_code)
    po_path = os.path.join(lang_dir, 'gui-subtrans.po')
    if not os.path.exists(po_path):
        now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M+0000')
        header = (
            'msgid ""\n'
            'msgstr ""\n'
            f'"Project-Id-Version: GPT-SubTrans\\n"\n'
            f'"POT-Creation-Date: {now}\\n"\n'
            f'"PO-Revision-Date: {now}\\n"\n'
            '"MIME-Version: 1.0\\n"\n'
            '"Content-Type: text/plain; charset=UTF-8\\n"\n'
            '"Content-Transfer-Encoding: 8bit\\n"\n'
            f'"Language: {language_code}\\n"\n'
        )
        with open(po_path, 'w', encoding='utf-8') as f:
            f.write(header)
    return po_path


def run_cmd(cmd: List[str]) -> None:
    try:
        subprocess.check_call(cmd)
    except FileNotFoundError:
        # gettext utils may be missing; skip gracefully
        print(f"Skipping: {' '.join(cmd)} (tool not found)")
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(cmd)} -> {e}")


def run_extract_strings() -> None:
    """Run scripts/extract_strings.py to refresh POT (and English PO)."""
    script = os.path.join(base_path, 'scripts', 'extract_strings.py')
    if not os.path.exists(script):
        print(f"extract_strings.py not found at {script}")
        return
    try:
        subprocess.check_call([sys.executable, script])
    except subprocess.CalledProcessError as e:
        print(f"extract_strings.py failed: {e}")


def merge_and_compile(languages: Optional[List[str]] = None):
    if not os.path.exists(POT_PATH):
        print(f"POT not found at {POT_PATH}. Run extract_strings.py first.")
        return

    # Get available languages dynamically
    languages = languages or get_available_locales()
    if not languages:
        print("No locales found. Please ensure locale directories exist in the locales folder.")
        return

    for lang in languages:
        po_path = ensure_po(lang)
        mo_path = os.path.splitext(po_path)[0] + '.mo'

        # Merge POT into PO (msgmerge)
        # Use --no-wrap to keep long msgid/msgstr on single lines so our
        # seeding/cleaning tools can operate reliably.
        run_cmd(['msgmerge', '--update', '--no-fuzzy-matching', '--backup=none', '--no-wrap', po_path, POT_PATH])

        # Post-merge normalization: collapse wrapped msgid lines in-place.
        try:
            if clean_po_file(po_path):
                print(f"Normalized msgid wrapping: {po_path}")
        except Exception as e:
            print(f"Warning: could not clean {po_path}: {e}")

        # Compile MO (msgfmt)
        run_cmd(['msgfmt', '-o', mo_path, po_path])

        print(f"Updated {po_path} and {mo_path}")


def _collect_untranslated_msgids(po_file_path: str) -> Dict[str, str]:
    """Parse a .po file and return a dict of msgid -> '' for empty msgstr entries."""
    untranslated: Dict[str, str] = {}
    try:
        with open(po_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        return untranslated

    current_msgid: Optional[str] = None
    current_msgstr: Optional[str] = None
    in_msgid = False
    in_msgstr = False

    for raw in lines:
        line = raw.strip()

        if line.startswith('msgid '):
            # finalize previous
            if current_msgid is not None and current_msgstr == "":
                untranslated[current_msgid] = ""

            current_msgid = line[len('msgid '):].strip('"')
            current_msgstr = None
            in_msgid = True
            in_msgstr = False
            continue

        if line.startswith('msgstr '):
            current_msgstr = line[len('msgstr '):].strip('"')
            in_msgstr = True
            in_msgid = False
            continue

        if line.startswith('"') and (in_msgid or in_msgstr):
            content = line.strip('"')
            if in_msgid and current_msgid is not None:
                current_msgid += content
            elif in_msgstr and current_msgstr is not None:
                current_msgstr += content
            continue

        if not line:
            if current_msgid is not None and current_msgstr == "":
                untranslated[current_msgid] = ""
            current_msgid = None
            current_msgstr = None
            in_msgid = in_msgstr = False
            continue

        if line.startswith('#~'):
            current_msgid = None
            current_msgstr = None
            in_msgid = in_msgstr = False

    if current_msgid is not None and current_msgstr == "":
        untranslated[current_msgid] = ""

    return untranslated


def write_untranslated_dict_file(lang: str, untranslated: Dict[str, str]) -> str:
    out_path = os.path.join(base_path, f'untranslated_msgids_{lang}.txt')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('{' + "\n")
        for key in untranslated.keys():
            escaped_key = key.replace("'", "\\'")
            f.write(f"    '{escaped_key}': '',\n")
        f.write('}' + "\n")
    return out_path


def generate_untranslated_files(languages: List[str]) -> None:
    for lang in languages:
        po_file = os.path.join(LOCALES_DIR, lang, 'LC_MESSAGES', 'gui-subtrans.po')
        untranslated = _collect_untranslated_msgids(po_file)
        out_path = write_untranslated_dict_file(lang, untranslated)
        print(f"Extracted {len(untranslated)} untranslated msgids to '{out_path}'.")


def _parse_manual_translations(path: str) -> Dict[str, str]:
    """Safely parse a dict-like file produced by write_untranslated_dict_file, returning only non-empty translations."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        data = ast.literal_eval(content)
        if not isinstance(data, dict):
            return {}
        # Keep only entries with non-empty translations
        return {str(k): str(v) for k, v in data.items() if isinstance(v, str) and v != ''}
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Warning: could not parse manual translations in {path}: {e}")
        return {}


def _update_po_with_translations(po_path: str, translations: Dict[str, str]) -> int:
    """Update msgstr for matching msgid entries. Returns count of updated entries."""
    if not translations:
        return 0

    try:
        with open(po_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        return 0

    out: List[str] = []
    i = 0
    updated = 0
    current_msgid: Optional[str] = None
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()

        if stripped.startswith('msgid '):
            # capture full msgid possibly spanning quoted lines
            indent_len = len(line) - len(stripped)
            indent = line[:indent_len]
            first_content = _extract_quoted(stripped) if '"' in stripped else ''
            j = i + 1
            parts = [first_content]
            while j < len(lines) and _is_quoted_line(lines[j]):
                parts.append(_extract_quoted(lines[j]))
                j += 1
            current_msgid = ''.join(parts)
            # write original msgid lines as-is (we don't rewrap here)
            out.extend(lines[i:j])
            i = j
            # next should be msgstr or comments/blank
            if i < len(lines):
                next_line = lines[i]
                nstrip = next_line.lstrip()
                if nstrip.startswith('msgstr '):
                    # collect existing msgstr continuation to know the block
                    msgstr_indent_len = len(next_line) - len(nstrip)
                    msgstr_indent = next_line[:msgstr_indent_len]
                    msgstr_first = _extract_quoted(nstrip) if '"' in nstrip else ''
                    k = i + 1
                    while k < len(lines) and _is_quoted_line(lines[k]):
                        k += 1

                    if current_msgid in translations and msgstr_first == '':
                        # Replace msgstr block with our translation (single line)
                        value = _escape_po(translations[current_msgid])
                        out.append(f"{msgstr_indent}msgstr \"{value}\"\n")
                        updated += 1
                        i = k
                        continue
                    else:
                        # keep original msgstr block untouched
                        out.extend(lines[i:k])
                        i = k
                        continue
                else:
                    # not a msgstr line; just continue
                    continue
            continue

        # default fall-through
        out.append(line)
        i += 1

    if updated:
        with open(po_path, 'w', encoding='utf-8') as f:
            f.writelines(out)
    return updated


def integrate_manual_translations(languages: List[str]) -> None:
    total_updated = 0
    for lang in languages:
        po_path = os.path.join(LOCALES_DIR, lang, 'LC_MESSAGES', 'gui-subtrans.po')
        dict_path = os.path.join(base_path, f'untranslated_msgids_{lang}.txt')
        translations = _parse_manual_translations(dict_path)
        if not translations:
            print(f"No manual translations found for {lang} (or none filled). Skipping.")
            continue
        updated = _update_po_with_translations(po_path, translations)
        if updated:
            total_updated += updated
            print(f"Integrated {updated} translations into {po_path}")
            # Compile after updates
            mo_path = os.path.splitext(po_path)[0] + '.mo'
            run_cmd(['msgfmt', '-o', mo_path, po_path])
        else:
            print(f"No matching empty entries updated for {lang}.")
    if total_updated:
        print(f"Integrated total {total_updated} translations across locales.")


def main():
    # 1) Extract strings -> POT
    print("[1/5] Extracting strings…")
    run_extract_strings()

    # discover locales
    languages = get_available_locales()
    print(f"Locales: {languages}")

    # 2) Merge & compile
    print("[2/5] Merging POT into PO and compiling…")
    merge_and_compile(languages)

    # 3) Integrate manual translations if present
    print("[3/5] Integrating any manual translations from untranslated_msgids_*.txt…")
    integrate_manual_translations(languages)

    # 4) Re-compile already handled inside integrate when updates occur

    # 5) Generate fresh untranslated files for all locales (remaining only)
    print("[4/5] Generating untranslated lists…")
    generate_untranslated_files(languages)
    print("[5/5] Done.")


if __name__ == '__main__':
    main()


