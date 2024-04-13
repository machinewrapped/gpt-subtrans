call envsubtrans/scripts/activate
python.exe -m pip install --upgrade pip
pip install pywin32-ctypes
pip install --upgrade pyinstaller
pip install --upgrade -r requirements.txt
pip install --upgrade openai
pip install --upgrade google.generativeai
pip install --upgrade anthropic
pyinstaller --noconfirm --additional-hooks-dir="PySubtitleHooks" --add-data "theme/*;theme/" --add-data "instructions*;instructions/" --add-data "LICENSE;." --add-data "assets/gui-subtrans.ico;." gui-subtrans.py
