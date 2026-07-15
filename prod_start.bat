@echo off
title Pinthesis Production Launcher
echo ==================================================
echo         Pinthesis Production Launcher
echo ==================================================
echo.

set /p ENABLE_BLUR="Enable Image Blurring? (y/n) [Default: y]: "

if /i "%ENABLE_BLUR%"=="n" (
    set VITE_DEV_BLUR=false
    echo Image blurring is DISABLED.
) else (
    set VITE_DEV_BLUR=true
    echo Image blurring is ENABLED.
)
echo.

set /p MODE="Launch Frontend in [W]eb mode or [T]auri desktop mode? (w/t) [Default: w]: "
echo.

echo Starting FastAPI Backend (Production)...
start "Pinthesis Backend" cmd /c "cd img-api && call C:\Users\peli\miniconda3\Scripts\activate.bat && uvicorn main:app --host 0.0.0.0 --port 8000"

echo Building Frontend...
cd vue-project
call npx pnpm build

if /i "%MODE%"=="t" (
    echo Building Tauri desktop app...
    call npx pnpm tauri build
    echo Launching Desktop Application...
    start "" "src-tauri\target\release\vue-project.exe"
) else (
    echo Starting Production Web Server...
    call npx pnpm preview --port 5173 --host 0.0.0.0
)

pause
