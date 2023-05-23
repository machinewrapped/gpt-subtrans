call envsubtrans/scripts/activate
pip install -r requirements.txt
pyinstaller --add-data "theme/*;theme/" --add-data "instructions*;." --add-data "LICENSE;." gui-subtrans.py
