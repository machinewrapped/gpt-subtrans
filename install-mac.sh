#!/bin/bash

echo "Checking if Python 3 is installed..."
command -v python3 >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Python 3 not found. Please install Python 3 and try again."
    exit 1
fi

echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2)
MIN_VERSION="3.10.0"

if [ "$(printf '%s\n' "$MIN_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$MIN_VERSION" ]; then 
    echo "Detected Python version is less than 3.10.0. Please upgrade your Python version."
    exit 1
fi

echo "Python version is 3.10.0 or higher."

echo "Checking if 'envsubtrans' folder exists..."
if [ -d "envsubtrans" ]; then
    echo "'envsubtrans' folder exists. Please delete it to continue with the installation."
    exit 1
fi

echo "Creating and activating virtual environment 'envsubtrans'..."
python3 -m venv envsubtrans
chmod +x ./envsubtrans/bin/activate 
source ./envsubtrans/bin/activate

echo "Installing requirements from 'requirements.txt'..."
pip install --platform=universal2 --no-deps --upgrade --target ./envsubtrans/lib -r requirements.txt

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

if [[ "$(echo "${free_plan}" | tr '[:lower:]' '[:upper:]')" == "Y" ]] || [[ "$(echo "${free_plan}" | tr '[:lower:]' '[:upper:]')" == "YES" ]]; then
    echo "MAX_THREADS=1" >> .env
    echo "RATE_LIMIT=5" >> .env
    echo "Warning: Translation speed will be severely limited due to the free plan limitations."
    echo "If you upgrade your plan, rerun the script to update your settings."
fi

echo "Installation complete."
echo "To uninstall, simply delete the directory."
