@echo off
SET script_name=%1.py
SET cmd_name=%1.cmd

echo Generating %cmd_name%...
echo @echo off > %cmd_name%
echo call envsubtrans\Scripts\activate.bat >> %cmd_name%
echo envsubtrans\Scripts\python.exe scripts\%script_name% %%* >> %cmd_name%
echo call envsubtrans\Scripts\deactivate >> %cmd_name%
