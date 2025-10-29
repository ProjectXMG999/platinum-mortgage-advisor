# PowerShell script to run Platinum Mortgage Advisor

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   PLATINUM MORTGAGE ADVISOR" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Aktywuj środowisko wirtualne
& ".\venv\Scripts\Activate.ps1"

# Uruchom aplikację
python src\main.py

# Dezaktywuj środowisko (automatyczne przy zamknięciu)
