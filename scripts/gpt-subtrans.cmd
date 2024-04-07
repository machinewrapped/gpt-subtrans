@echo off

rem Activate the virtual environment
call envsubtrans\Scripts\activate.bat

rem Check for script selection and run the appropriate script with the provided arguments
if "%~1" == "" (
    rem No arguments provided, run the default script
    python gui-subtrans.py
) else if "%~1" == "clause" (
    shift
    python claude-subtrans.py %*
) else if "%~1" == "gemini" (
    shift
    python gemini-subtrans.py %*
) else if "%~1" == "gpt" (
    shift
    python gpt-subtrans.py %*
) else (
    echo Invalid option: %~1 >&2
    exit /b 1
)

rem Deactivate the virtual environment
call envsubtrans\Scripts\deactivate
