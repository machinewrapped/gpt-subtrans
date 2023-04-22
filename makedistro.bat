call envsubtrans/scripts/activate
pyinstaller --add-data "theme/*;theme/" --add-data "instructions.txt;." --add-data "LICENSE;." gui-subtrans.py
