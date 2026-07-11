@echo off
title Pinthesis Dev Starter
echo ==================================================
echo         Pinthesis Development Launcher
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

echo Starting FastAPI Backend...
start "Pinthesis Backend" cmd /c "cd img-api && start.bat"

echo Starting Vue Frontend...
cd vue-project
if /i "%MODE%"=="t" (
    echo Running pnpm tauri dev...
    pnpm tauri dev
) else (
    echo Running npm run dev...
    npm run dev
)

pause
