@echo off
setlocal EnableDelayedExpansion

REM --- Check for winget ---
echo Checking for winget package manager...
winget --version >nul 2>&1
if !errorlevel! neq 0 (
    set "has_winget=0"
    echo Winget not found. Automatic installation of dependencies is not available.
) else (
    set "has_winget=1"
    echo Winget found.
)
echo.

REM --- Check for uv ---
echo Checking for uv...
uv --version >nul 2>&1
if !errorlevel! neq 0 (
    echo uv is not installed or not in your PATH.
    if "!has_winget!"=="1" (
        CHOICE /C YN /M "uv is a fast Python package manager. Do you want to install it using winget? (Y/N)"
        if !errorlevel! equ 1 (
            echo Installing uv...
            winget install -e --id astral-sh.uv
            echo.
            echo uv installation has been requested. Please close this window and run the script again once the installation is complete.
            pause
            goto :eof
        )
    )
    echo Please install uv manually by following the instructions at https://astral.sh/uv/install.sh
    pause
    goto :eof
)
echo uv found.
echo.

REM --- Check for Surge ---
echo Checking for Surge CLI...
surge --version >nul 2>&1
if !errorlevel! neq 0 (
    echo Surge CLI is not installed or not in your PATH.
    if "!has_winget!"=="1" (
        CHOICE /C YN /M "Surge is a high-performance downloader. Do you want to install it using winget? (Y/N)"
        if !errorlevel! equ 1 (
            echo Installing Surge...
            winget install surge-downloader.surge
            echo.
            echo Surge installation has been requested. Please close this window and run the script again once the installation is complete.
            pause
            goto :eof
        )
    )
    echo Please install Surge manually: winget install surge-downloader.surge
    pause
    goto :eof
)
echo Surge found.
echo.

REM --- Install Python requirements using uv ---
echo Installing required Python packages using uv...
uv sync
if !errorlevel! neq 0 (
    echo Error: Failed to install Python packages using uv.
    pause
    goto :eof
)
echo Requirements installed successfully.
echo.

REM --- Run the application ---
echo Starting the main application with uv...
uv run python main.py %*

REM --- Cleanup ---
echo.
echo Application finished.

endlocal
