@echo off
setlocal

call install.bat

call envsubtrans\Scripts\activate.bat

echo Installing Mistral SDK...
pip install -U mistralai

if not exist .env (
    REM Create .env file
    echo Creating .env file to hold environment variables
    echo PROVIDER=Mistral > .env
) else (
    REM Remove existing PROVIDER and add PROVIDER=Mistral
    type .env | findstr /v "^PROVIDER=" > temp.env
    echo PROVIDER=Mistral >> temp.env
    move /y temp.env .env > nul
)

REM Check if MISTRAL provider settings are already configured
findstr /m "MISTRAL_API_KEY" .env > nul
if not errorlevel 1 (
    echo Found MISTRAL_API_KEY in .env file
    goto skip_api_key
)

echo Please enter your Mistral API key
set /p api_key=MISTRAL_API_KEY:

if not "%api_key%"=="" (
    echo MISTRAL_API_KEY=%api_key% >> .env
    echo API key saved to .env
) else (
    echo No API key entered. Skipping API key configuration.
)

:skip_api_key

call scripts\generate-cmd.bat gpt-subtrans

echo default provider set to Mistral

echo Installation complete. To uninstall, simply delete the directory.
exit /b 0
