#!/usr/bin/env python3
"""
Extract translatable strings from the source tree and write locales/gui-subtrans.pot.

Rules:
- _("text") → msgid "text"
- tr("context", "text") → msgctxt "context" ; msgid "text"

Only constant string literals are extracted.
"""
import ast
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BASE_DIR)
POT_PATH = os.path.join(BASE_DIR, 'gui-subtrans.pot')

INCLUDE_DIRS = (
    'GUI',
    'PySubtitle',
    'scripts',
)
EXCLUDE_DIRS = (
    'locales',
    'PySubtitle/UnitTests',
    'Tests',
    'assets',
    'theme',
    'PySubtitleHooks',
)


def ensure_parent(path: str):
    parent = os.path.dirname(path)
    os.makedirs(parent, exist_ok=True)


def should_include(path: str) -> bool:
    rel = os.path.relpath(path, REPO_ROOT).replace('\\', '/')
    if not rel.endswith('.py'):
        return False
    for ex in EXCLUDE_DIRS:
        if rel.startswith(ex.rstrip('/') + '/') or rel == ex:
            return False
    return any(rel.startswith(d.rstrip('/') + '/') or rel == d for d in INCLUDE_DIRS)


def escape_po(s: str) -> str:
    return s.replace('\\', r'\\').replace('"', r'\"').replace('\n', r'\n')


def collect_entries() -> Dict[Tuple[Optional[str], str], List[Tuple[str, int]]]:
    entries: Dict[Tuple[Optional[str], str], List[Tuple[str, int]]] = {}

    for root, _, files in os.walk(REPO_ROOT):
        for name in files:
            path = os.path.join(root, name)
            if not should_include(path):
                continue
            rel = os.path.relpath(path, REPO_ROOT).replace('\\', '/')
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    source = f.read()
                tree = ast.parse(source, filename=rel)

                for node in ast.walk(tree):
                    if not isinstance(node, ast.Call):
                        continue
                    func = node.func
                    func_name = None
                    if isinstance(func, ast.Name):
                        func_name = func.id
                    elif isinstance(func, ast.Attribute):
                        func_name = func.attr
                    if func_name not in ('_', 'tr'):
                        continue

                    # Extract arguments
                    if func_name == '_' and node.args:
                        arg = node.args[0]
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                            key = (None, arg.value)
                        else:
                            continue
                    elif func_name == 'tr' and len(node.args) >= 2:
                        ctx_arg, txt_arg = node.args[0], node.args[1]
                        if (
                            isinstance(ctx_arg, ast.Constant) and isinstance(ctx_arg.value, str)
                            and isinstance(txt_arg, ast.Constant) and isinstance(txt_arg.value, str)
                        ):
                            key = (ctx_arg.value, txt_arg.value)
                        else:
                            continue
                    else:
                        continue

                    entries.setdefault(key, []).append((rel, node.lineno))

            except Exception:
                # Ignore parse/IO errors for extraction purposes
                continue

    return entries


def write_pot(entries: Dict[Tuple[Optional[str], str], List[Tuple[str, int]]]):
    ensure_parent(POT_PATH)
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M+0000')

    lines: List[str] = []
    # Header
    lines.append('msgid ""')
    lines.append('msgstr ""')
    lines.append(f'"Project-Id-Version: GPT-SubTrans\\n"')
    lines.append(f'"POT-Creation-Date: {now}\\n"')
    lines.append(f'"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"')
    lines.append(f'"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"')
    lines.append(f'"MIME-Version: 1.0\\n"')
    lines.append(f'"Content-Type: text/plain; charset=UTF-8\\n"')
    lines.append(f'"Content-Transfer-Encoding: 8bit\\n"')
    lines.append(f'"Language: en\\n"')
    lines.append('')

    for (context, msgid), refs in sorted(entries.items(), key=lambda k: (k[0][0] or '', k[0][1])):
        # References
        ref_chunks = [f"{f}:{n}" for f, n in sorted(refs)]
        if ref_chunks:
            lines.append(f"#: {' '.join(ref_chunks)}")
        if context:
            lines.append(f"msgctxt \"{escape_po(context)}\"")
        lines.append(f"msgid \"{escape_po(msgid)}\"")
        lines.append("msgstr \"\"")
        lines.append("")

    with open(POT_PATH, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    print(f"Wrote {POT_PATH} with {len(entries)} entries")


def main():
    entries = collect_entries()
    write_pot(entries)


if __name__ == '__main__':
    main()


