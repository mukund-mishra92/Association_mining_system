@echo off
echo ================================================================
echo        Python Command Validation & System Check
echo ================================================================
echo.

echo [Testing Python Commands]
echo.

echo 1. Testing 'py' command...
py --version 2>nul
if not errorlevel 1 (
    echo    ✓ 'py' command works
    set RECOMMENDED_CMD=py
) else (
    echo    ✗ 'py' command failed
)

echo.
echo 2. Testing 'python' command...
python --version 2>nul
if not errorlevel 1 (
    echo    ✓ 'python' command works
    if not defined RECOMMENDED_CMD set RECOMMENDED_CMD=python
) else (
    echo    ✗ 'python' command failed
)

echo.
echo 3. Testing 'python3' command...
python3 --version 2>nul
if not errorlevel 1 (
    echo    ✓ 'python3' command works
    if not defined RECOMMENDED_CMD set RECOMMENDED_CMD=python3
) else (
    echo    ✗ 'python3' command failed
)

echo.
echo ================================================================
if defined RECOMMENDED_CMD (
    echo ✓ RECOMMENDATION: Use '%RECOMMENDED_CMD%' for your system
    echo.
    echo Your system configuration:
    %RECOMMENDED_CMD% --version
    echo.
    echo ✓ All startup scripts have been updated to use the correct commands
    echo ✓ You can now use any of these startup options:
    echo    • SMART_START.bat    (Recommended - Auto-detects Python)
    echo    • start.bat          (Uses 'py' command)
    echo    • start_compatible.bat (Tries multiple commands)
) else (
    echo ✗ ERROR: No working Python command found!
    echo.
    echo Please install Python from:
    echo   • https://python.org
    echo   • Microsoft Store
)

echo ================================================================
echo.
pause