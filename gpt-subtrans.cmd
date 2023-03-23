@echo off

rem Activate the virtual environment
call subtrans-env\Scripts\activate.bat

rem Run the script with the provided arguments
python gpt-subtrans.py %*

rem Deactivate the virtual environment
call subtrans-env\Scripts\deactivate
