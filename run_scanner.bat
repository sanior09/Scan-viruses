@echo off
title [ NACHAPOL INDUSTRIES - JARVIS OS v4.0 ]
color 0e
chcp 65001 >nul

:: กำหนดตำแหน่งไฟล์โครงการหลักอัตโนมัติตามโฟลเดอร์ปัจจุบัน
set "SCANNER_DIR=%~dp0"
cd /d "%SCANNER_DIR%"

echo [*] INITIALIZING JARVIS INTERFACE...
echo [*] CHECKING SYSTEM DEPENDENCIES...
:: คอมเมนต์บรรทัดติดตั้งออก เพื่อป้องกันหน้าต่างค้างระหว่างบูทระบบ
:: pip install yara-python tqdm python-dotenv psutil py7zr rarfile watchdog requests

echo.
echo [*] ACTIVATING SELF-DEFENSE PROTOCOL...
start /min "Watchdog" python "Watchdog.py"

echo.
echo [*] LOADING DEFENSE HUD...
python "Dashboard.py"

echo.
echo [*] PROTOCOL EXECUTED SUCCESSFULLY.
pause
