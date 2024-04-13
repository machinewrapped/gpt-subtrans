#!/bin/bash

source ./envsubtrans/bin/activate
pip3 install --upgrade pip
pip install --upgrade --target ./envsubtrans/lib pyinstaller
pip install --upgrade --target ./envsubtrans/lib charset_normalizer
pip install --upgrade --target ./envsubtrans/lib -r requirements.txt
pip install --upgrade --target ./envsubtrans/lib openai
pip install --upgrade --target ./envsubtrans/lib google.generativeai
pip install --upgrade --target ./envsubtrans/lib anthropic
pip install --upgrade --target ./envsubtrans/lib PySide6==6.6.0
pip install --upgrade --target ./envsubtrans/lib PySide6.QtGui

pyinstaller --noconfirm --additional-hooks-dir="PySubtitleHooks" --hidden-import="PySide6.QtGui" --paths="./envsubtrans/lib" --paths="./envsubtrans/lib/python3.12/site-packages" --add-data "theme/*:theme/" --add-data "instructions*:instructions/" --add-data "LICENSE:." --add-data "assets/gui-subtrans.ico:." --noconfirm scripts/gui-subtrans.py
