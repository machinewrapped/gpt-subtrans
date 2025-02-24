#!/bin/bash

source envsubtrans/bin/activate
pip install -r requirements.txt
pip install --upgrade openai
pip install --upgrade google-genai
pip install --upgrade anthropic
pip install --upgrade mistralai
pip install --upgrade boto3

pyinstaller --noconfirm --additional-hooks-dir="PySubtitleHooks" --add-data "theme/*:theme/"  --add-data "assets/*:assets/" --add-data "instructions*:instructions/" --add-data "LICENSE:." --add-data "assets/gui-subtrans.ico:." scripts/gui-subtrans.py
