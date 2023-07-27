#!/bin/bash

source envsubtrans/bin/activate
pip install --platform=universal2 --no-deps --upgrade --target ./envsubtrans/lib pyinstaller
pip install --upgrade -r requirements.txt
pip install --platform=universal2 --no-deps --upgrade --target ./envsubtrans/lib regex
pip install --platform=universal2 --no-deps --upgrade --target ./envsubtrans/lib srt
pip install --platform=universal2 --no-deps --upgrade --target ./envsubtrans/lib charset_normalizer
pip install --platform=universal2 --no-deps --upgrade --target ./envsubtrans/lib multidict
pip install --platform=universal2 --no-deps --upgrade --target ./envsubtrans/lib aiohttp
pyinstaller --paths="./envsubtrans/lib" --add-data "theme/*:theme/" --add-data "instructions*:." --add-data "LICENSE:." --target-arch universal2 --noconfirm gui-subtrans.py
