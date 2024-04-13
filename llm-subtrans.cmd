@echo off 
call envsubtrans\Scripts\activate.bat 
python scripts\llm-subtrans.py %* 
call envsubtrans\Scripts\deactivate 
