#!/usr/bin/env python3
"""
Simple string extraction script for GUI-SubTrans localization
Extracts strings marked with _() for translation
"""
import os
import re
import sys
from pathlib import Path

def extract_strings_from_file(file_path):
    """Extract translatable strings from a Python file"""
    strings = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Simple regex to find _("string") and _('string') patterns
        patterns = [
            r'_\(\s*"([^"\\]*(?:\\.[^"\\]*)*)"\s*\)',  # _("string")
            r"_\(\s*'([^'\\]*(?:\\.[^'\\]*)*)'\s*\)",  # _('string')
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                string_content = match.group(1)
                # Unescape the string
                string_content = string_content.encode().decode('unicode_escape')
                strings.append(string_content)
    
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return strings

def create_pot_file(strings, output_path):
    """Create a .pot template file"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('# GUI-SubTrans Translation Template\n')
        f.write('# \n')
        f.write('msgid ""\n')
        f.write('msgstr ""\n')
        f.write('"Content-Type: text/plain; charset=UTF-8\\n"\n')
        f.write('"Language: \\n"\n\n')
        
        for string in sorted(set(strings)):
            if string.strip():  # Skip empty strings
                f.write(f'msgid "{string}"\n')
                f.write('msgstr ""\n\n')

def main():
    # Get the project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Find Python files in GUI and PySubtitle directories
    gui_dir = project_root / "GUI"
    pysubtitle_dir = project_root / "PySubtitle"
    
    all_strings = []
    
    # Extract from GUI files
    if gui_dir.exists():
        for py_file in gui_dir.rglob("*.py"):
            strings = extract_strings_from_file(py_file)
            all_strings.extend(strings)
            if strings:
                print(f"Found {len(strings)} strings in {py_file}")
    
    # Extract from PySubtitle files
    if pysubtitle_dir.exists():
        for py_file in pysubtitle_dir.rglob("*.py"):
            strings = extract_strings_from_file(py_file)
            all_strings.extend(strings)
            if strings:
                print(f"Found {len(strings)} strings in {py_file}")
    
    print(f"\nTotal unique strings found: {len(set(all_strings))}")
    
    # Create the .pot file
    pot_path = script_dir / "gui-subtrans.pot"
    create_pot_file(all_strings, pot_path)
    print(f"Created template file: {pot_path}")

if __name__ == "__main__":
    main()