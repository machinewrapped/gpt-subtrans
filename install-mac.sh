#!/bin/bash
# Enable error handling
set -e

echo "Checking if Python 3 is installed..."
if ! python3 --version &>/dev/null; then
    echo "Python 3 not found. Please install Python 3 and try again."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
MIN_VERSION="3.10.0"

if [[ "$(printf '%s\n' "$MIN_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$MIN_VERSION" ]]; then
    echo "Detected Python version is less than 3.10.0. Please upgrade your Python version."
    exit 1
else
    echo "Python version is compatible."
fi

echo "Checking if \"envsubtrans\" folder exists..."
if [ -d "envsubtrans" ]; then
    echo "\"envsubtrans\" folder already exists."
    echo "Do you want to perform a clean install? This will delete the existing environment. (Y/N)"
    read -p "Enter your choice (Y/N): " user_choice
    if [ "$user_choice" = "Y" ] || [ "$user_choice" = "y" ]; then
        echo "Performing a clean install..."
        rm -rf envsubtrans
        [ -f .env ] && rm .env
    elif [ "$user_choice" != "N" ] && [ "$user_choice" != "n" ]; then
        echo "Invalid choice. Exiting installation."
        exit 1
    fi
else
    echo "Creating \"envsubtrans\" directory..."
fi

python3 -m venv envsubtrans
source envsubtrans/bin/activate

# Check if .env exists and contains a line that starts with "PROVIDER="
if [ -f ".env" ] && grep -q "^PROVIDER=" .env; then
    echo "Provider configuration found in .env file."
else
    echo "Select which provider you want to install:"
    echo "1 = OpenAI"
    echo "2 = Google Gemini"
    read -p "Enter your choice (1/2): " provider_choice

    case $provider_choice in
        1)
            read -p "Enter your OpenAI API Key: " openai_api_key
            echo "PROVIDER=OpenAI" > .env
            echo "OPENAI_API_KEY=$openai_api_key" >> .env
            echo "Installing OpenAI module..."
            pip install openai
            ;;
        2)
            read -p "Enter your Google Gemini API Key: " gemini_api_key
            echo "PROVIDER=Gemini" > .env
            echo "GEMINI_API_KEY=$gemini_api_key" >> .env
            echo "Installing Google GenerativeAI module..."
            pip install google-generativeai
            ;;
        *)
            echo "Invalid choice. Exiting installation."
            exit 1
            ;;
    esac
fi

echo "Installing requirements from \"requirements.txt\"..."
pip install -r requirements.txt

echo "Setup completed successfully. To uninstall just delete the directory"

exit 0
