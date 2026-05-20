@echo off
setlocal EnableDelayedExpansion
title PromptRefiner — Setup
color 0A

echo.
echo  ================================================
echo    PromptRefiner — One-Click Setup
echo  ================================================
echo.

:: ── Check Python ─────────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found.
    echo.
    echo  Please install Python 3.10 or newer from:
    echo    https://www.python.org/downloads/
    echo.
    echo  IMPORTANT: Check "Add Python to PATH" during installation.
    echo.
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
for /f "tokens=1,2 delims=." %%a in ("%PYVER%") do (
    set PYMAJ=%%a
    set PYMIN=%%b
)
if %PYMAJ% LSS 3 goto oldpython
if %PYMAJ% EQU 3 if %PYMIN% LSS 10 goto oldpython
echo  [OK] Python %PYVER% found.
goto pythonok

:oldpython
echo  [ERROR] Python %PYVER% is too old. Please install Python 3.10 or newer.
start https://www.python.org/downloads/
pause
exit /b 1

:pythonok

:: ── Create virtual environment ───────────────────────────────────────────────
echo.
echo  [1/4] Creating virtual environment...
if exist venv (
    echo       Already exists, skipping.
) else (
    python -m venv venv
    if errorlevel 1 (
        echo  [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo  [OK] Virtual environment created.
)

:: ── Activate venv ────────────────────────────────────────────────────────────
call venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet

:: ── Install main dependencies ─────────────────────────────────────────────────
echo.
echo  [2/4] Installing dependencies (this may take a few minutes)...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo  [ERROR] Failed to install dependencies. Check your internet connection.
    pause
    exit /b 1
)
echo  [OK] Dependencies installed.

:: ── Install llama-cpp-python (local AI, GPU-aware) ───────────────────────────
echo.
echo  [3/4] Installing local AI support...

set LLAMA_INSTALLED=0

:: Check for NVIDIA GPU
nvidia-smi >nul 2>&1
if not errorlevel 1 (
    echo       NVIDIA GPU detected — installing CUDA build...
    pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121 --quiet
    if not errorlevel 1 set LLAMA_INSTALLED=1
)

:: Check for AMD GPU (Vulkan)
if %LLAMA_INSTALLED%==0 (
    wmic path win32_videocontroller get name 2>nul | findstr /i "AMD Radeon" >nul
    if not errorlevel 1 (
        echo       AMD GPU detected — installing Vulkan build...
        pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/vulkan --quiet
        if not errorlevel 1 set LLAMA_INSTALLED=1
    )
)

:: Fallback: CPU build
if %LLAMA_INSTALLED%==0 (
    echo       Installing CPU build (works on all machines)...
    pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu --quiet
    if not errorlevel 1 set LLAMA_INSTALLED=1
)

if %LLAMA_INSTALLED%==1 (
    echo  [OK] Local AI model support installed.
) else (
    echo  [WARN] Local AI not installed. Cloud providers ^(Groq/Cerebras^) will still work.
)

:: ── Create launcher ───────────────────────────────────────────────────────────
echo.
echo  [4/4] Creating launcher...

:: run.bat — used by desktop shortcut
(
    echo @echo off
    echo cd /d "%%~dp0"
    echo call venv\Scripts\activate.bat
    echo start "" pythonw main.py
) > run.bat

:: Desktop shortcut
set SHORTCUT=%USERPROFILE%\Desktop\PromptRefiner.lnk
set RUNBAT=%CD%\run.bat
powershell -NoProfile -Command ^
  "$s=(New-Object -COM WScript.Shell).CreateShortcut('%SHORTCUT%');" ^
  "$s.TargetPath='%RUNBAT%';" ^
  "$s.WorkingDirectory='%CD%';" ^
  "$s.Description='PromptRefiner — AI text refinement';" ^
  "$s.Save()"

echo  [OK] Desktop shortcut created.

:: ── Done ─────────────────────────────────────────────────────────────────────
echo.
echo  ================================================
echo    Setup complete!
echo.
echo    Launch PromptRefiner from your desktop,
echo    or double-click run.bat anytime.
echo.
echo    On first launch the app appears in your
echo    system tray. Press Alt+Shift+W anywhere
echo    to refine selected text.
echo  ================================================
echo.
pause
exit /b 0
