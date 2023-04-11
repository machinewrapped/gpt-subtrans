#!/bin/bash

echo "Checking if Python 3 is installed..."
if ! command -v python3 &> /dev/null; then
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
    echo "Please enter your API key:"
    read -r api_key

    if [ -n "$api_key" ]; then
        echo "API_KEY=$api_key" > .env
        echo "API key saved to .env"
    fi
else
    echo ".env file already exists, skipping API key input."
fi

echo "Installation complete."
echo "To uninstall, simply delete the 'envsubtrans' folder."
