@echo off
setlocal enabledelayedexpansion

echo Checking if Python 3 is installed...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python 3 not found. Please install Python 3 and try again.
    exit /b 1
)

echo Checking if "envsubtrans" folder exists...
if exist envsubtrans (
    echo "envsubtrans" folder exists. Please delete it to continue with the installation.
    exit /b 1
)

echo Creating and activating virtual environment "envsubtrans"...
python -m venv envsubtrans
call envsubtrans\Scripts\activate.bat

echo Installing requirements from "requirements.txt"...
pip install -r requirements.txt

if not exist .env (
    echo Please enter your OpenAI API key:
    set /p api_key=API_KEY:

    if not "!api_key!"=="" (
        echo API_KEY=!api_key! > .env
        echo API key saved to .env
    )
) else (
    echo .env file already exists, skipping API key input.
)

echo Installation complete.
echo To uninstall, simply delete the directory.
exit /b 0
