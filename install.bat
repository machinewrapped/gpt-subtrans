@echo off
setlocal enabledelayedexpansion

echo Checking if Python 3 is installed...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python 3 not found. Please install Python 3 and try again.
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
set MIN_VERSION=3.10.0

python -c "import sys; sys.exit(not (tuple(map(int, '%PYTHON_VERSION%'.split('.'))) >= tuple(map(int, '%MIN_VERSION%'.split('.')))))"
if errorlevel 1 (
    echo Detected Python version is less than 3.10.0. Please upgrade your Python version.
    exit /b 1
)

echo Python version is compatible.

echo Checking if "envsubtrans" folder exists...
if exist envsubtrans (
    echo "envsubtrans" folder already exists.
    echo Do you want to perform a clean install? This will delete the existing environment. (Y/N)
    set /p user_choice=Enter your choice (Y/N): 
    if /i "!user_choice!"=="Y" (
        echo Performing a clean install...
        rmdir /s /q envsubtrans
        python -m venv envsubtrans
        call envsubtrans\Scripts\activate.bat
        echo Installing requirements from "requirements.txt"...
        pip install -r requirements.txt
    ) else if /i "!user_choice!"=="N" (
        call envsubtrans\Scripts\activate.bat
        echo Updating requirements in the existing environment...
        pip install -U -r requirements.txt
    ) else (
        echo Invalid choice. Exiting installation.
        exit /b 1
    )
) else (
    echo Creating and activating virtual environment "envsubtrans"...
    python -m venv envsubtrans
    call envsubtrans\Scripts\activate.bat
    echo Installing requirements from "requirements.txt"...
    pip install -r requirements.txt
)

echo Please enter your OpenAI API key:
set /p api_key=OPENAI_API_KEY:

if not "!api_key!"=="" (
    echo OPENAI_API_KEY=!api_key! > .env
    echo API key saved to .env
)

echo Please enter your OpenAI API host (Leave blank for default: https://api.openai.com/v1):
set /p api_base=OPENAI_API_BASE:

if not "!api_base!"=="" (
    echo OPENAI_API_BASE=!api_base! >> .env
    echo API base saved to .env
)

echo Are you on the free plan? (Y/N)
set /p free_plan=Free plan?:

if /i "!free_plan!"=="Y" (
    set add_limits=1
) else if /i "!free_plan!"=="Yes" (
    set add_limits=1
) else (
    set add_limits=0
)

if "!add_limits!"=="1" (
    echo OPENAI_FREE_PLAN=1 >> .env
    echo Warning: Translation speed will be severely limited due to the free plan limitations.
    echo If you upgrade your plan, rerun the script to update your settings.
)

echo Installation complete.
echo To uninstall, simply delete the directory.
exit /b 0
