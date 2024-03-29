@echo off

rem Activate the virtual environment
call envsubtrans\Scripts\activate.bat

rem Run the script with the provided arguments
python claude-subtrans.py %*

rem Deactivate the virtual environment
call envsubtrans\Scripts\deactivate
