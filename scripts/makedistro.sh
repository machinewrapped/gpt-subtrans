#!/bin/bash

source envsubtrans/bin/activate
pip install -r requirements.txt
pip install --upgrade openai
pip install --upgrade google-genai
pip install --upgrade anthropic
pip install --upgrade mistralai
pip install --upgrade boto3

python scripts/update_translations.py

pyinstaller --noconfirm --additional-hooks-dir="PySubtitleHooks" --add-data "theme/*:theme/"  --add-data "assets/*:assets/" --add-data "instructions*:instructions/" --add-data "LICENSE:." --add-data "assets/gui-subtrans.ico:." --add-data "locales/*:locales/" scripts/gui-subtrans.py
