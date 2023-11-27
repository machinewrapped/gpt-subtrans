#!/bin/bash

source ./envsubtrans/bin/activate
pip install --platform=universal2 --no-deps --upgrade --target ./envsubtrans/lib pyinstaller
pip install --platform=universal2 --no-deps --upgrade --target ./envsubtrans/lib -r requirements.txt
pip install --platform=universal2 --no-deps --upgrade --target ./envsubtrans/lib charset_normalizer
pip install --upgrade --target ./envsubtrans/lib pydantic_core
pip install --upgrade --target ./envsubtrans/lib pyside6
#pyinstaller --paths="./envsubtrans/lib" --paths="./envsubtrans/lib/python3.12/site-packages"  --add-data "theme/*:theme/" --add-data "instructions*:." --add-data "LICENSE:." --add-data "gui-subtrans.ico:." --target-arch universal2 --noconfirm gui-subtrans.py
pyinstaller --paths="./envsubtrans/lib" --paths="./envsubtrans/lib/python3.12/site-packages" --add-data "theme/*:theme/" --add-data "instructions*:." --add-data "LICENSE:." --add-data "gui-subtrans.ico:." --noconfirm gui-subtrans.py
