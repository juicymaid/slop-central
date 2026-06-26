@echo off
call C:\Users\peli\miniconda3\Scripts\activate.bat
uvicorn main:app --host 0.0.0.0 --reload --reload-exclude ./files/
pause