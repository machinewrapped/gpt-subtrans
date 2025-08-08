#!/usr/bin/env python3
"""
Simple script to compile .po files to .mo files
"""
import os
import subprocess
import sys
from pathlib import Path

def compile_po_file(po_path, mo_path):
    """Compile a .po file to .mo file using Python's msgfmt functionality"""
    try:
        # Try using the built-in msgfmt module first
        import msgfmt
        with open(po_path, 'rb') as po_file:
            po_data = po_file.read()
        mo_data = msgfmt.pofile_to_mofile(po_data)
        with open(mo_path, 'wb') as mo_file:
            mo_file.write(mo_data)
        return True
    except ImportError:
        # Fallback to system msgfmt if available
        try:
            result = subprocess.run(['msgfmt', '-o', str(mo_path), str(po_path)], 
                                    capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Manual implementation as last resort
            return compile_po_manual(po_path, mo_path)

def compile_po_manual(po_path, mo_path):
    """Manual compilation of .po to .mo file"""
    import struct
    
    translations = {}
    
    try:
        with open(po_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Simple parser for .po files
        entries = content.split('\n\n')
        for entry in entries:
            lines = entry.strip().split('\n')
            msgid = None
            msgstr = None
            
            for line in lines:
                if line.startswith('msgid '):
                    msgid = line[7:-1] if line[6] == '"' else line[6:]
                elif line.startswith('msgstr '):
                    msgstr = line[8:-1] if line[7] == '"' else line[7:]
                elif line.startswith('"') and msgstr is not None:
                    msgstr += line[1:-1]
            
            if msgid and msgstr and msgid != '':
                translations[msgid] = msgstr
        
        # Create .mo file format
        keys = list(translations.keys())
        values = list(translations.values())
        
        # Encode strings
        kencoded = [k.encode('utf-8') for k in keys]
        vencoded = [v.encode('utf-8') for v in values]
        
        # Create the .mo file structure
        keyoffsets = []
        valueoffsets = []
        output = []
        
        # Calculate offsets
        offset = 7 * 4 + 16 * len(keys)
        for k in kencoded:
            keyoffsets.append(offset)
            offset += len(k) + 1
        for v in vencoded:
            valueoffsets.append(offset)
            offset += len(v) + 1
        
        # Write the .mo file
        with open(mo_path, 'wb') as f:
            # Magic number
            f.write(struct.pack('<I', 0x950412de))
            # Version
            f.write(struct.pack('<I', 0))
            # Number of entries
            f.write(struct.pack('<I', len(keys)))
            # Offset of key table
            f.write(struct.pack('<I', 7 * 4))
            # Offset of value table  
            f.write(struct.pack('<I', 7 * 4 + 8 * len(keys)))
            # Hash table size
            f.write(struct.pack('<I', 0))
            # Offset of hash table
            f.write(struct.pack('<I', 0))
            
            # Write key table
            for i, k in enumerate(kencoded):
                f.write(struct.pack('<I', len(k)))
                f.write(struct.pack('<I', keyoffsets[i]))
            
            # Write value table
            for i, v in enumerate(vencoded):
                f.write(struct.pack('<I', len(v)))
                f.write(struct.pack('<I', valueoffsets[i]))
            
            # Write keys and values
            for k in kencoded:
                f.write(k)
                f.write(b'\0')
            for v in vencoded:
                f.write(v)
                f.write(b'\0')
        
        return True
    
    except Exception as e:
        print(f"Error compiling {po_path}: {e}")
        return False

def main():
    script_dir = Path(__file__).parent
    
    for lang_dir in script_dir.iterdir():
        if lang_dir.is_dir() and lang_dir.name != '__pycache__':
            lc_messages = lang_dir / 'LC_MESSAGES'
            if lc_messages.exists():
                po_file = lc_messages / 'gui-subtrans.po'
                mo_file = lc_messages / 'gui-subtrans.mo'
                
                if po_file.exists():
                    print(f"Compiling {po_file} -> {mo_file}")
                    success = compile_po_file(po_file, mo_file)
                    if success:
                        print(f"Successfully compiled {lang_dir.name}")
                    else:
                        print(f"Failed to compile {lang_dir.name}")

if __name__ == "__main__":
    main()