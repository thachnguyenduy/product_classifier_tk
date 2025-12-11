@echo off
REM ============================================
REM RUN SCRIPT - Coca-Cola Sorting System (Windows)
REM ============================================

echo ===========================================
echo   COCA-COLA SORTING SYSTEM
echo   FIFO Queue Mode
echo ===========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
)

echo [OK] Python found
echo.

REM Check dependencies
echo Checking dependencies...
python -c "import cv2, numpy, serial, PIL" 2>nul
if errorlevel 1 (
    echo [ERROR] Missing dependencies!
    echo Run: pip install -r requirements.txt
    pause
    exit /b 1
)

echo [OK] Dependencies OK
echo.

REM Check NCNN (optional)
python -c "import ncnn" 2>nul
if errorlevel 1 (
    echo [WARNING] NCNN not found - will use dummy fallback
) else (
    echo [OK] NCNN OK
)

echo.
echo Starting system...
echo ===========================================
echo.

REM Run main script
python main.py

echo.
echo System stopped.
pause

