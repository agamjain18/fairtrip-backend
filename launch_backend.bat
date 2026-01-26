@echo off
:: FairTrip Backend - Automatic Server Starter & Firewall Configurator
:: This script requires Administrator privileges to modify firewall rules.

title FairTrip Backend - Initializing...

:: --- ELEVATION CHECK ---
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Running with Administrator privileges.
) else (
    echo [ERROR] This script requires Administrator privileges.
    echo Attempting to restart as Administrator...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: --- FIREWALL CONFIGURATION ---
echo.
echo [1/3] Configuring Windows Firewall...

:: 1. Allow Python to communicate on the local network
netsh advfirewall firewall add rule name="FairTrip_Backend_Python" dir=in action=allow program="python.exe" enable=yes profile=any
netsh advfirewall firewall add rule name="FairTrip_Backend_Python" dir=out action=allow program="python.exe" enable=yes profile=any

:: 2. Specifically unblock Port 8000 (Backend)
netsh advfirewall firewall add rule name="FairTrip_Port_8000" dir=in action=allow protocol=TCP localport=8000 enable=yes profile=any

:: 3. The "Active All Ports" Request - Open port range for local development
:: WARNING: This allows communication on all ports for local development. Only use on trusted networks.
echo [!] Activating all ports for local development (as requested)...
netsh advfirewall firewall add rule name="FairTrip_All_Dev_Ports" dir=in action=allow protocol=TCP localport=0-65535 enable=yes profile=any

echo [SUCCESS] Firewall rules updated. Mobile devices can now connect to your local IP.

:: --- RUN BACKEND SERVER ---
echo.
echo [2/3] Checking dependencies...
where python >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b
)

echo [3/3] Starting FairTrip Backend Server on http://0.0.0.0:8000...
echo.

:: Ensure we are in the correct directory
cd /d "%~dp0"

:: Start the server
python main.py

if %errorLevel% neq 0 (
    echo.
    echo [ERROR] Backend failed to start. Ensure main.py exists and dependencies are installed.
    pause
)
