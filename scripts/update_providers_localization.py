#!/usr/bin/env python3
"""
Batch update all provider files to add localization imports and wrap GetOptions strings.
"""
import os
import re

# Add the parent directory to sys.path so we can import PySubtitle modules
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
providers_dir = os.path.join(base_path, 'PySubtitle', 'Providers')

def update_provider_file(provider_path):
    """Update a provider file to add localization support"""
    with open(provider_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Skip if already has localization import
    if 'from PySubtitle.Helpers.Localization import _' in content:
        print(f"SKIP: {os.path.basename(provider_path)} already has localization import")
        return False
    
    # Pattern 1: Add localization import after other PySubtitle.Helpers imports
    helpers_pattern = r'(\s+from PySubtitle\.Helpers import [^\n]+)'
    if re.search(helpers_pattern, content):
        content = re.sub(
            helpers_pattern,
            r'\1\n        from PySubtitle.Helpers.Localization import _',
            content,
            count=1
        )
        print(f"ADDED: localization import to {os.path.basename(provider_path)} after Helpers import")
    else:
        # Pattern 2: Add before first PySubtitle import  
        pysubtitle_pattern = r'(\s+)(from PySubtitle\.[^L][^\n]+)'
        if re.search(pysubtitle_pattern, content):
            content = re.sub(
                pysubtitle_pattern,
                r'\1from PySubtitle.Helpers.Localization import _\n\1\2',
                content,
                count=1
            )
            print(f"ADDED: localization import to {os.path.basename(provider_path)} before PySubtitle imports")
    
    # Pattern 3: Wrap strings in GetOptions method
    # Find GetOptions method and wrap all string literals in tuples
    def replace_option_strings(match):
        method_content = match.group(0)
        
        # Replace (str, "text") with (str, _("text"))
        method_content = re.sub(
            r"\(str,\s*\"([^\"]+)\"\)",
            r'(str, _("\1"))',
            method_content
        )
        
        # Replace (int, "text") with (int, _("text"))
        method_content = re.sub(
            r"\(int,\s*\"([^\"]+)\"\)",
            r'(int, _("\1"))',
            method_content
        )
        
        # Replace (float, "text") with (float, _("text"))
        method_content = re.sub(
            r"\(float,\s*\"([^\"]+)\"\)",
            r'(float, _("\1"))',
            method_content
        )
        
        # Replace (bool, "text") with (bool, _("text"))
        method_content = re.sub(
            r"\(bool,\s*\"([^\"]+)\"\)",
            r'(bool, _("\1"))',
            method_content
        )
        
        # Replace (list, "text") with (list, _("text"))
        method_content = re.sub(
            r"\(\[([^\]]+)\],\s*\"([^\"]+)\"\)",
            r'([\1], _("\2"))',
            method_content
        )
        
        return method_content
    
    # Find and update GetOptions method
    getoptions_pattern = r'def GetOptions\(self\)[^:]*:.*?(?=\n    def|\n        class|\nclass|\Z)'
    if re.search(getoptions_pattern, content, re.DOTALL):
        content = re.sub(
            getoptions_pattern,
            replace_option_strings,
            content,
            flags=re.DOTALL
        )
        print(f"UPDATED: GetOptions strings in {os.path.basename(provider_path)}")
    
    # Write back if changed
    if content != original_content:
        with open(provider_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    else:
        print(f"NO CHANGE: {os.path.basename(provider_path)}")
        return False

def main():
    """Update all provider files"""
    provider_files = [f for f in os.listdir(providers_dir) if f.startswith('Provider_') and f.endswith('.py')]
    
    updated_count = 0
    for provider_file in sorted(provider_files):
        provider_path = os.path.join(providers_dir, provider_file)
        if update_provider_file(provider_path):
            updated_count += 1
    
    print(f"\nSUCCESS: Updated {updated_count} out of {len(provider_files)} provider files")

if __name__ == '__main__':
    main()