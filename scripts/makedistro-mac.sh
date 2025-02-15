#!/bin/bash

source ./envsubtrans/bin/activate
pip3 install --upgrade pip
pip install --upgrade pyinstaller
pip install --upgrade PyInstaller pyinstaller-hooks-contrib
pip install --upgrade setuptools
pip install --upgrade jaraco.text
pip install --upgrade charset_normalizer
pip install --upgrade -r requirements.txt
pip install --upgrade openai
pip install --upgrade google-genai
pip install --upgrade anthropic
pip install --upgrade mistralai

# Remove boto3 from packaged version
pip uninstall boto3

python tests/unit_tests.py
if [ $? -ne 0 ]; then
    echo "Unit tests failed. Exiting..."
    exit $?
fi

./envsubtrans/bin/pyinstaller --noconfirm --additional-hooks-dir="PySubtitleHooks" --paths="./envsubtrans/lib" --add-data "theme/*:theme/" --add-data "assets/*:assets/"  --add-data "instructions*:instructions/" --add-data "LICENSE:." --noconfirm scripts/gui-subtrans.py
