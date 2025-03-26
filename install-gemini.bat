@echo off
setlocal

call install.bat

call envsubtrans\Scripts\activate.bat

echo Installing Google Gemini SDK...
pip install -U google-genai google-api-core

if not exist .env (
    REM Create .env file
    echo Creating .env file to hold environment variables
    echo PROVIDER=Gemini > .env
) else (
    REM Remove existing PROVIDER and add PROVIDER=Gemini
    type .env | findstr /v "^PROVIDER=" > temp.env
    echo PROVIDER=Gemini >> temp.env
    move /y temp.env .env > nul
)

REM Check if GEMINI provider settings are already configured
findstr /m "GEMINI_API_KEY" .env > nul
if not errorlevel 1 (
    echo Found GEMINI_API_KEY in .env file
    goto skip_api_key
)

echo Please enter your Google Gemini API key:
set /p api_key=GEMINI_API_KEY:

if not "%api_key%"=="" (
    echo GEMINI_API_KEY=%api_key% >> .env
    echo API key saved to .env
)

:skip_api_key

call scripts\generate-cmd.bat gemini-subtrans

echo default provider set to Google Gemini

echo Installation complete. To uninstall, simply delete the directory.
exit /b 0
