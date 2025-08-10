import os
import sys

# Add the parent directory to sys.path so we can import PySubtitle modules
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_path)

from PySubtitle.Helpers.Localization import get_available_locales

def extract_untranslated_msgids(po_file_path, output_file_path):
    """
    Reads a .po file, extracts msgids that do not have a translation (empty msgstr),
    and writes them to an output file in a dictionary-ready format.
    """
    untranslated_msgids_dict = {}
    
    try:
        with open(po_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: The file '{po_file_path}' was not found.")
        return

    current_msgid = None
    current_msgstr = None
    in_msgid_block = False
    in_msgstr_block = False

    for line in lines:
        stripped_line = line.strip()

        if stripped_line.startswith("msgid "):
            if current_msgid is not None and current_msgstr == "":
                untranslated_msgids_dict[current_msgid] = ""
            
            current_msgid = stripped_line[len("msgid "):].strip('"')
            current_msgstr = None
            in_msgid_block = True
            in_msgstr_block = False

        elif stripped_line.startswith("msgstr "):
            current_msgstr = stripped_line[len("msgstr "):].strip('"')
            in_msgstr_block = True
            in_msgid_block = False

        elif stripped_line.startswith('"') and (in_msgid_block or in_msgstr_block):
            content_part = stripped_line.strip('"')
            if in_msgid_block:
                current_msgid += content_part
            elif in_msgstr_block:
                current_msgstr += content_part

        elif not stripped_line and current_msgid is not None:
            if current_msgstr == "":
                untranslated_msgids_dict[current_msgid] = ""
            
            current_msgid = None
            current_msgstr = None
            in_msgid_block = False
            in_msgstr_block = False

        elif stripped_line.startswith("#~"):
            current_msgid = None
            current_msgstr = None
            in_msgid_block = False
            in_msgstr_block = False
        
    if current_msgid is not None and current_msgstr == "":
        untranslated_msgids_dict[current_msgid] = ""

    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write("{\n")
        for key, value in untranslated_msgids_dict.items():
            escaped_key = key.replace("'", "\\'")
            f.write(f"    '{escaped_key}': '{value}',\n")
        f.write("}\n")

    print(f"Extracted {len(untranslated_msgids_dict)} untranslated msgids to '{output_file_path}' in dictionary format.")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Accept command line argument for language, or process all available locales
    if len(sys.argv) > 1:
        target_langs = [sys.argv[1]]
        # Verify the language exists
        available_locales = get_available_locales()
        if target_langs[0] not in available_locales:
            print(f"Language '{target_langs[0]}' not found in available locales: {available_locales}")
            print(f"Usage: python {sys.argv[0]} [language_code]")
            sys.exit(1)
    else:
        # Process all available locales
        target_langs = get_available_locales()
        print(f"No language specified, processing all available locales: {target_langs}")
    
    for target_lang in target_langs:
        print(f"\nProcessing language: {target_lang}")
        po_file = os.path.join(base_dir, 'locales', target_lang, 'LC_MESSAGES', 'gui-subtrans.po')
        output_file = os.path.join(base_dir, f'untranslated_msgids_{target_lang}.txt')
        
        extract_untranslated_msgids(po_file, output_file)
