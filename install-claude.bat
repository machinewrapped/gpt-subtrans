@echo off
setlocal

call install.bat

call envsubtrans\Scripts\activate.bat

echo Installing Anthropic Claude SDK...
pip install -U anthropic

if not exist .env (
    REM Create .env file
    echo Creating .env file to hold environment variables
    echo PROVIDER=Claude > .env
) else (
    REM Remove existing PROVIDER and add PROVIDER=Claude
    type .env | findstr /v "^PROVIDER=" > temp.env
    echo PROVIDER=Claude >> temp.env
    move /y temp.env .env > nul
)

REM Check if CLAUDE provider settings are already configured
findstr /m "CLAUDE_API_KEY" .env > nul
if not errorlevel 1 (
    echo Found CLAUDE_API_KEY in .env file
    goto skip_api_key
)

echo Please enter your Anthropic Claude API key:
set /p api_key=CLAUDE_API_KEY:

if not "%api_key%"=="" (
    echo CLAUDE_API_KEY=%api_key% >> .env
    echo API key saved to .env
)

:skip_api_key

echo default provider set to Anthropic Claude

echo Installation complete. To uninstall, simply delete the directory.
exit /b 0
