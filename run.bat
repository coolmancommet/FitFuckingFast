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

REM --- Check for aria2c ---
echo Checking for aria2c...
aria2c --version >nul 2>&1
if !errorlevel! neq 0 (
    echo aria2c is not installed or not in your PATH.
    if "!has_winget!"=="1" (
        CHOICE /C YN /M "Do you want to install aria2c using winget? (Y/N)"
        if !errorlevel! equ 1 (
            echo Installing aria2c...
            winget install -e --id aria2.aria2
            echo.
            echo aria2c installation has been requested. Please close this window and run the script again once the installation is complete.
            pause
            goto :eof
        )
    )
    echo Please download aria2c manually from https://github.com/aria2/aria2/releases and add it to your PATH.
    pause
    goto :eof
)
echo aria2c found.
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
echo Starting aria2c daemon...
start "aria2c_daemon" /min aria2c --enable-rpc --rpc-listen-all

timeout /t 3 /nobreak >nul

echo Starting the main application with uv...
uv run python main.py %*

REM --- Cleanup ---
echo.
echo Application finished. Closing aria2c daemon...
taskkill /IM aria2c.exe /F >nul 2>&1

endlocal