#!/usr/bin/env python3
"""
Script to update translation files from source code
"""
import os
import sys
from pathlib import Path

def main():
    script_dir = Path(__file__).parent
    os.chdir(script_dir.parent)
    
    print("Step 1: Extracting strings from source code...")
    os.system('python locales/extract_strings.py')
    
    print("\nStep 2: Compiling translation files...")
    os.system('python locales/compile_translations.py')
    
    print("\nTranslation update complete!")
    print("\nTo add new languages:")
    print("1. Create directory: locales/LANG/LC_MESSAGES/")
    print("2. Copy gui-subtrans.pot to gui-subtrans.po in that directory")
    print("3. Translate the strings in the .po file")
    print("4. Run this script again to compile")

if __name__ == "__main__":
    main()