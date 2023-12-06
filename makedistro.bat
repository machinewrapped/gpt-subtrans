call envsubtrans/scripts/activate
pip install --upgrade -r requirements.txt
pyinstaller --add-data "theme/*;theme/" --add-data "instructions*;." --add-data "LICENSE;." --add-data "gui-subtrans.ico;." gui-subtrans.py
