@echo off
setlocal

call install.bat

call envsubtrans\Scripts\activate.bat

echo Installing OpenAI SDK...
pip install -U openai^>=1.1.0

if not exist .env (
    REM Create .env file
    echo Creating .env file to hold environment variables
    echo PROVIDER=OpenAI > .env
) else (
    REM Remove existing PROVIDER and add PROVIDER=OpenAI
    type .env | findstr /v "^PROVIDER=" > temp.env
    echo PROVIDER=OpenAI >> temp.env
    move /y temp.env .env > nul
)

REM Check if OPENAI provider settings are already configured
findstr /m "OPENAI_API_KEY" .env > nul
if not errorlevel 1 (
    echo Found OPENAI_API_KEY in .env file
    goto skip_api_key
)

echo Please enter your OpenAI API key
set /p api_key=OPENAI_API_KEY:

if not "%api_key%"=="" (
    echo OPENAI_API_KEY=%api_key% >> .env
    echo API key saved to .env
) else (
    echo No API key entered. Skipping API key configuration.
)

echo Please enter your OpenAI API host URL (Leave blank for default)
set /p api_base=OPENAI_API_BASE:

if not "%api_base%"=="" (
    echo OPENAI_API_BASE=%api_base% >> .env
    echo API base saved to .env
)

echo Are you on the free plan? (Y/N)
set /p free_plan=Free plan?:

if /i "%free_plan%"=="Y" (
    echo OPENAI_FREE_PLAN=1 >> .env
    echo Warning: Translation speed will be severely limited due to the free plan limitations.
)

:skip_api_key

echo default provider set to OpenAI

echo Installation complete. To uninstall, simply delete the directory.
exit /b 0
