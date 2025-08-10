#!/usr/bin/env python3
"""
Update translations from POT into PO files and compile MO catalogs.

Also normalizes msgid wrapping inside PO files to single-line form so
seeding/matching works reliably.
"""
import os
import sys
import subprocess
from datetime import datetime, timezone
from typing import List

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


def merge_and_compile():
    if not os.path.exists(POT_PATH):
        print(f"POT not found at {POT_PATH}. Run extract_strings.py first.")
        return

    # Get available languages dynamically
    languages = get_available_locales()
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


def main():
    merge_and_compile()


if __name__ == '__main__':
    main()


