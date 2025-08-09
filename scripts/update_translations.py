#!/usr/bin/env python3
"""
Update translations from POT into PO files and compile MO catalogs.
"""
import os
import subprocess
from datetime import datetime
from typing import List

# Add the parent directory to sys.path so we can import PySubtitle modules
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOCALES_DIR = os.path.join(base_path, 'locales')
POT_PATH = os.path.join(LOCALES_DIR, 'gui-subtrans.pot')
LANGUAGES = ('en', 'es')


def ensure_dirs(language_code: str) -> str:
    lang_dir = os.path.join(LOCALES_DIR, language_code, 'LC_MESSAGES')
    os.makedirs(lang_dir, exist_ok=True)
    return lang_dir


def ensure_po(language_code: str) -> str:
    lang_dir = ensure_dirs(language_code)
    po_path = os.path.join(lang_dir, 'gui-subtrans.po')
    if not os.path.exists(po_path):
        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M+0000')
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

    for lang in LANGUAGES:
        po_path = ensure_po(lang)
        mo_path = os.path.splitext(po_path)[0] + '.mo'

        # Merge POT into PO (msgmerge)
        run_cmd(['msgmerge', '--update', '--no-fuzzy-matching', '--backup=none', po_path, POT_PATH])

        # Compile MO (msgfmt)
        run_cmd(['msgfmt', '-o', mo_path, po_path])

        print(f"Updated {po_path} and {mo_path}")


def main():
    merge_and_compile()


if __name__ == '__main__':
    main()


