#!/bin/bash

echo "Checking if Python 3 is installed..."
command -v python3 >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Python 3 not found. Please install Python 3 and try again."
    exit 1
fi

echo "Checking if 'envsubtrans' folder exists..."
if [ -d "envsubtrans" ]; then
    echo "'envsubtrans' folder exists. Please delete it to continue with the installation."
    exit 1
fi

echo "Creating and activating virtual environment 'envsubtrans'..."
python3 -m venv envsubtrans
source envsubtrans/bin/activate

echo "Installing requirements from 'requirements.txt'..."
pip install -r requirements.txt

if [ ! -f ".env" ]; then
    echo "Please enter your OpenAI API key:"
    read -r api_key
    echo "API_KEY=$api_key" > .env
    echo "API key saved to .env"
fi

echo "Please enter your OpenAI API host(Leave blank for default: https://api.openai.com/v1):"
read -r api_base
if [ ! -z "$api_base" ]; then
    echo "API_BASE=$api_base" >> .env
    echo "API base saved to .env"
fi

echo "Are you on the free plan? (Y/N)"
read -r free_plan

if [[ "${free_plan^^}" == "Y" ]] || [[ "${free_plan^^}" == "YES" ]]; then
    echo "MAX_THREADS=1" >> .env
    echo "RATE_LIMIT=5" >> .env
    echo "Warning: Translation speed will be severely limited due to the free plan limitations."
    echo "If you upgrade your plan, rerun the script to update your settings."
fi

echo "Installation complete."
echo "To uninstall, simply delete the directory."
