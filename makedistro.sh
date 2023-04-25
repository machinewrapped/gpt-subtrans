#!/bin/bash

source envsubtrans/scripts/activate
pip install -r requirements.txt
pyinstaller --add-data "theme/*:theme/" --add-data "instructions.txt:." --add-data "LICENSE:." gui-subtrans.py
