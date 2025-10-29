@echo off
REM Skrypt uruchamiający Platinum Mortgage Advisor

echo ========================================
echo   PLATINUM MORTGAGE ADVISOR
echo ========================================
echo.

REM Aktywuj środowisko wirtualne
call venv\Scripts\activate.bat

REM Uruchom aplikację
python src\main.py

REM Dezaktywuj środowisko
deactivate
