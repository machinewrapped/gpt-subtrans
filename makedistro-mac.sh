#!/bin/bash

source ./envsubtrans/bin/activate
pip3 install --upgrade pip
pip install --upgrade --target ./envsubtrans/lib pyinstaller
pip install --upgrade --target ./envsubtrans/lib charset_normalizer
pip install --upgrade --target ./envsubtrans/lib pydantic_core
pip install --upgrade --target ./envsubtrans/lib PySide6.QtGui
pip install --upgrade --target ./envsubtrans/lib -r requirements.txt
#pyinstaller --paths="./envsubtrans/lib" --paths="./envsubtrans/lib/python3.12/site-packages"  --add-data "theme/*:theme/" --add-data "instructions*:." --add-data "LICENSE:." --add-data "gui-subtrans.ico:." --target-arch universal2 --noconfirm gui-subtrans.py
pyinstaller --noconfirm --additional-hooks-dir="PySubtitleHooks" --hidden-import="PySide6.QtGui" --paths="./envsubtrans/lib" --paths="./envsubtrans/lib/python3.12/site-packages" --add-data "theme/*:theme/" --add-data "instructions*:." --add-data "LICENSE:." --add-data "gui-subtrans.ico:." --noconfirm gui-subtrans.py
