#!/usr/bin/env python3
"""
Extract translatable strings from the source tree and write locales/gui-subtrans.pot.

This version can import provider classes to extract their settings as well.

Rules:
- _("text") → msgid "text"
- tr("context", "text") → msgctxt "context" ; msgid "text"
- Setting keys from Options.py → auto-generated English translations
- Provider setting keys → extracted from providers with descriptions

Only constant string literals are extracted from source code.
"""
import ast
import os
import sys
import importlib
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

# Add the parent directory to sys.path so we can import PySubtitle modules
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_path)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = base_path

from PySubtitle.TranslationProvider import TranslationProvider

LOCALES_DIR = os.path.join(REPO_ROOT, 'locales')
POT_PATH = os.path.join(LOCALES_DIR, 'gui-subtrans.pot')

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


def generate_english_name(key: str) -> str:
    """Generate English display name from setting key using the same logic as OptionWidget.GenerateName"""
    # Guard: setting keys must not contain format placeholders
    if '{' in key or '}' in key:
        raise ValueError(f"Invalid setting key for English name generation (contains braces): {key}")
    import re
    name = key.replace('_', ' ').title()
    # Preserve common initialisms after title-casing
    replacements = {
        r"\bApi\b": "API",
        r"\bAws\b": "AWS",
        r"\bUrl\b": "URL",
        r"\bUri\b": "URI",
        r"\bUi\b": "UI",
    }
    for pattern, repl in replacements.items():
        name = re.sub(pattern, repl, name)
    return name


def extract_setting_keys(entries: Dict[Tuple[Optional[str], str], List[Tuple[str, int]]]):
    """
    Extract all setting keys from PySubtitle/Options.py default_options dictionary
    and add them as translatable strings.
    """
    options_path = os.path.join(REPO_ROOT, 'PySubtitle', 'Options.py')
    
    try:
        with open(options_path, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source, filename='PySubtitle/Options.py')
        
        # Find the default_options dictionary
        for node in ast.walk(tree):
            if (isinstance(node, ast.Assign) and 
                len(node.targets) == 1 and
                isinstance(node.targets[0], ast.Name) and 
                node.targets[0].id == 'default_options' and
                isinstance(node.value, ast.Dict)):
                
                # Extract all dictionary keys
                for key_node in node.value.keys:
                    if isinstance(key_node, ast.Constant) and isinstance(key_node.value, str):
                        setting_key = key_node.value
                        # Add as translatable string
                        key = (None, setting_key)
                        entries.setdefault(key, []).append(('PySubtitle/Options.py', key_node.lineno))
                        
    except Exception as e:
        print(f"Warning: Could not extract setting keys from Options.py: {e}")


def extract_provider_settings(entries: Dict[Tuple[Optional[str], str], List[Tuple[str, int]]]):
    """
    Extract setting keys from all translation providers by importing them
    and examining their __init__ methods and GetOptions() methods.
    """
    providers_dir = os.path.join(REPO_ROOT, 'PySubtitle', 'Providers')
    
    # Find all Provider_*.py files
    provider_files = []
    for file in os.listdir(providers_dir):
        if file.startswith('Provider_') and file.endswith('.py'):
            provider_files.append(file)
    
    print(f"Found {len(provider_files)} provider files: {provider_files}")
    
    for provider_file in provider_files:
        provider_path = os.path.join(providers_dir, provider_file)
        provider_name = provider_file[:-3]  # Remove .py extension
        
        try:
            # Extract settings statically first
            static_keys = extract_provider_settings_static(provider_path)
            
            # Try to extract settings dynamically
            dynamic_keys = extract_provider_settings_dynamic(provider_name)
            
            # Combine both approaches
            all_keys = static_keys | dynamic_keys
            
            for key in all_keys:
                # Add as translatable string without context (all providers share same key translations)
                entry_key = (None, key)
                entries.setdefault(entry_key, []).append((f'PySubtitle/Providers/{provider_file}', 0))
                
        except Exception as e:
            print(f"Warning: Could not extract settings from {provider_file}: {e}")


def extract_provider_settings_static(provider_path: str) -> set[str]:
    """
    Statically parse provider __init__ method to extract setting keys.
    """
    keys = set()
    
    try:
        with open(provider_path, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source)
        
        # Look for __init__ method in provider class
        for node in ast.walk(tree):
            if (isinstance(node, ast.FunctionDef) and 
                node.name == '__init__'):
                
                # Look for super().__init__ call with settings dict
                for child in ast.walk(node):
                    if (isinstance(child, ast.Call) and
                        isinstance(child.func, ast.Attribute) and
                        child.func.attr == '__init__' and
                        len(child.args) >= 2):
                        
                        # The second argument should be a dict with settings
                        settings_arg = child.args[1]
                        if isinstance(settings_arg, ast.Dict):
                            for key_node in settings_arg.keys:
                                if isinstance(key_node, ast.Constant) and isinstance(key_node.value, str):
                                    keys.add(key_node.value)
                                elif isinstance(key_node, ast.Str):  # Python < 3.8 compatibility
                                    keys.add(key_node.s)
                        
    except Exception as e:
        print(f"Warning: Static analysis failed for {provider_path}: {e}")
    
    return keys


def extract_provider_settings_dynamic(provider_name: str) -> set[str]:
    """
    Try to dynamically import provider and call GetOptions() to extract settings.
    """
    keys = set()
    
    try:
        # Suppress provider warnings/errors during import
        original_level = logging.getLogger().level
        logging.getLogger().setLevel(logging.CRITICAL)
        
        # Import the provider module
        module_name = f'PySubtitle.Providers.{provider_name}'
        module = importlib.import_module(module_name)
        
        # Find the provider class
        provider_class = getattr(module, provider_name, None)
        if provider_class and issubclass(provider_class, TranslationProvider):
            
            # Try to instantiate with minimal settings
            try:
                instance = provider_class({})
                options = instance.GetOptions()
                keys.update(options.keys())
                print(f"Dynamic extraction from {provider_name}: {list(keys)}")
                
            except Exception:
                # Provider might need specific settings, try with some common ones
                try:
                    dummy_settings = {
                        'api_key': 'dummy_key_for_extraction',
                        'model': 'dummy_model',
                    }
                    instance = provider_class(dummy_settings)
                    options = instance.GetOptions()
                    keys.update(options.keys())
                    print(f"Dynamic extraction from {provider_name} (with dummy settings): {list(keys)}")
                    
                except Exception as e:
                    print(f"Dynamic extraction failed for {provider_name}: {e}")
        
    except ImportError as e:
        print(f"Could not import {provider_name}: {e}")
    except Exception as e:
        print(f"Error with {provider_name}: {e}")
    finally:
        # Restore original logging level
        logging.getLogger().setLevel(original_level)
    
    return keys


def collect_entries() -> Dict[Tuple[Optional[str], str], List[Tuple[str, int]]]:
    entries: Dict[Tuple[Optional[str], str], List[Tuple[str, int]]] = {}
    setting_keys = set()

    # Auto-extract setting keys from Options.py
    extract_setting_keys(entries)
    # Collect setting keys from Options.py
    options_path = os.path.join(REPO_ROOT, 'PySubtitle', 'Options.py')
    try:
        with open(options_path, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source, filename='PySubtitle/Options.py')
        for node in ast.walk(tree):
            if (isinstance(node, ast.Assign) and 
                len(node.targets) == 1 and
                isinstance(node.targets[0], ast.Name) and 
                node.targets[0].id == 'default_options' and
                isinstance(node.value, ast.Dict)):
                for key_node in node.value.keys:
                    if isinstance(key_node, ast.Constant) and isinstance(key_node.value, str):
                        setting_keys.add(key_node.value)
                    elif isinstance(key_node, ast.Str):
                        setting_keys.add(key_node.s)
    except Exception:
        pass

    # Auto-extract provider setting keys
    providers_dir = os.path.join(REPO_ROOT, 'PySubtitle', 'Providers')
    provider_files = [f for f in os.listdir(providers_dir) if f.startswith('Provider_') and f.endswith('.py')]
    for provider_file in provider_files:
        provider_path = os.path.join(providers_dir, provider_file)
        try:
            # Extract settings statically first
            static_keys = extract_provider_settings_static(provider_path)
            # Try to extract settings dynamically
            dynamic_keys = extract_provider_settings_dynamic(provider_file[:-3])
            all_keys = static_keys | dynamic_keys
            for key in all_keys:
                setting_keys.add(key)
        except Exception:
            pass
    extract_provider_settings(entries)

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
                continue

    # Attach setting_keys to entries for downstream use
    entries['__setting_keys__'] = list(setting_keys)
    return entries


def write_pot(entries: Dict[Tuple[Optional[str], str], List[Tuple[str, int]]]):
    ensure_parent(POT_PATH)
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M+0000')

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

    for key, refs in sorted(entries.items(), key=lambda k: (k[0][0] or '', k[0][1]) if isinstance(k[0], tuple) else ('', '')):
        if not isinstance(key, tuple) or len(key) != 2:
            continue
        context, msgid = key
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
    
    # Also write English PO with auto-generated setting names
    write_english_po(entries, now)


def write_english_po(entries: Dict[Tuple[Optional[str], str], List[Tuple[str, int]]], timestamp: str):
    """Write English PO file with auto-generated translations for setting keys"""
    en_po_path = os.path.join(LOCALES_DIR, 'en', 'LC_MESSAGES', 'gui-subtrans.po')
    ensure_parent(en_po_path)
    
    # Only auto-generate msgstr for setting keys (Options.py or Providers), all others blank
    lines: List[str] = []

    # Header
    lines.append('msgid ""')
    lines.append('msgstr ""')
    lines.append(f'"Project-Id-Version: GPT-SubTrans\\n"')
    lines.append(f'"POT-Creation-Date: {timestamp}\\n"')
    lines.append(f'"PO-Revision-Date: {timestamp}\\n"')
    lines.append(f'"Last-Translator: Auto-generated\\n"')
    lines.append(f'"MIME-Version: 1.0\\n"')
    lines.append(f'"Content-Type: text/plain; charset=UTF-8\\n"')
    lines.append(f'"Content-Transfer-Encoding: 8bit\\n"')
    lines.append(f'"Language: en\\n"')
    lines.append('')


    # Extract setting_keys from entries
    setting_keys = set(entries.pop('__setting_keys__', []))

    for key, refs in sorted(entries.items(), key=lambda k: (k[0][0] or '', k[0][1]) if isinstance(k[0], tuple) else ('', '')):
        if not isinstance(key, tuple) or len(key) != 2:
            continue
        context, msgid = key
        # References
        ref_chunks = [f"{f}:{n}" for f, n in sorted(refs)]
        if ref_chunks:
            lines.append(f"#: {' '.join(ref_chunks)}")
        if context:
            lines.append(f"msgctxt \"{escape_po(context)}\"")
        lines.append(f"msgid \"{escape_po(msgid)}\"")

        # Only auto-generate for actual setting keys (context must be None, msgid in setting_keys, and msgid looks like a key)
        if context is None and msgid in setting_keys and msgid.isidentifier():
            msgstr = generate_english_name(msgid)
        else:
            msgstr = ""

        lines.append(f"msgstr \"{escape_po(msgstr)}\"")
        lines.append("")

    with open(en_po_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    print(f"Wrote {en_po_path} with auto-generated setting translations (sanitized)")


def main():
    entries = collect_entries()
    write_pot(entries)


if __name__ == '__main__':
    main()