#!/bin/bash

source envsubtrans/bin/activate
pip install --platform=universal2 --no-deps --upgrade --target ./envsubtrans/lib pyinstaller
pip install --platform=universal2 --no-deps --upgrade --force-reinstall --target ./envsubtrans/lib -r requirements.txt
pyinstaller --paths="./envsubtrans/lib" --add-data "theme/*:theme/" --add-data "instructions*:." --add-data "LICENSE:." --target-arch universal2 --noconfirm gui-subtrans.py
