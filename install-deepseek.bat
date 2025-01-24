@echo off
setlocal

call install.bat

call envsubtrans\Scripts\activate.bat

echo Installing OpenAI SDK...
pip install -U openai^>=1.1.0

if not exist .env (
    REM Create .env file
    echo Creating .env file to hold environment variables
    echo PROVIDER=DeepSeek > .env
) else (
    REM Remove existing PROVIDER and add PROVIDER=DeepSeek
    type .env | findstr /v "^PROVIDER=" > temp.env
    echo PROVIDER=DeepSeek >> temp.env
    move /y temp.env .env > nul
)

REM Check if DEEPSEEK provider settings are already configured
findstr /m "DEEPSEEK_API_KEY" .env > nul
if not errorlevel 1 (
    echo Found DEEPSEEK_API_KEY in .env file
    goto skip_api_key
)

echo Please enter your DeepSeek API key
set /p api_key=DEEPSEEK_API_KEY:

if not "%api_key%"=="" (
    echo DEEPSEEK_API_KEY=%api_key% >> .env
    echo API key saved to .env
) else (
    echo No API key entered. Skipping API key configuration.
)

echo Please enter your DeepSeek API host URL (Leave blank for default)
set /p api_base=DEEPSEEK_API_BASE:

if not "%api_base%"=="" (
    echo DEEPSEEK_API_BASE=%api_base% >> .env
    echo API base saved to .env
)

:skip_api_key

call scripts\generate-cmd.bat deepseek-subtrans

echo default provider set to DeepSeek

echo Installation complete. To uninstall, simply delete the directory.
exit /b 0
