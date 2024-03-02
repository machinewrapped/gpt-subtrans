call envsubtrans/scripts/activate
pip install pywin32-ctypes
pip install --upgrade pyinstaller
pip install --upgrade -r requirements.txt
pyinstaller --noconfirm --additional-hooks-dir="PySubtitleHooks" --add-data "theme/*;theme/" --add-data "instructions*;." --add-data "LICENSE;." --add-data "gui-subtrans.ico;." gui-subtrans.py
