#!/bin/bash

source envsubtrans/bin/activate
pip install -r requirements.txt
pyinstaller --noconfirm --additional-hooks-dir="PySubtitleHooks" --add-data "theme/*:theme/" --add-data "instructions*:." --add-data "LICENSE:." --add-data "assets/gui-subtrans.ico:." gui-subtrans.py
