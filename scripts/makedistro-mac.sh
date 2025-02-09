#!/bin/bash

source ./envsubtrans/bin/activate
pip3 install --upgrade pip
pip install --upgrade --target ./envsubtrans/lib pyinstaller
pip install --upgrade --target ./envsubtrans/lib PyInstaller pyinstaller-hooks-contrib
pip install --upgrade --target ./envsubtrans/lib charset_normalizer
pip install --upgrade --target ./envsubtrans/lib -r requirements.txt
pip install --upgrade --target ./envsubtrans/lib openai
pip install --upgrade --target ./envsubtrans/lib google-genai
pip install --upgrade --target ./envsubtrans/lib anthropic
pip install --upgrade --target ./envsubtrans/lib mistralai
pip install --upgrade --target ./envsubtrans/lib boto3
pip install --upgrade --target ./envsubtrans/lib PySide6==6.6.0
pip install --upgrade --target ./envsubtrans/lib PySide6.QtGui

python tests/unit_tests.py
if [ $? -ne 0 ]; then
    echo "Unit tests failed. Exiting..."
    exit $?
fi

pyinstaller --noconfirm --additional-hooks-dir="PySubtitleHooks" --hidden-import="PySide6.QtGui" --hidden-import="pkg_resources.extern" --paths="./envsubtrans/lib" --paths="./envsubtrans/lib/python3.12/site-packages" --add-data "theme/*:theme/" --add-data "assets/*:assets/"  --add-data "instructions*:instructions/" --add-data "LICENSE:." --noconfirm scripts/gui-subtrans.py
