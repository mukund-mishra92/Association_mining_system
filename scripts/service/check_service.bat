@echo off
REM Check Association Mining System Service Status

echo ========================================
echo Association Mining Service Status
echo ========================================
echo.

REM Query service status
sc query AssociationMiningService

if %errorLevel% == 0 (
    echo.
    echo ========================================
    echo Service Information
    echo ========================================
    echo.
    echo Service Name: AssociationMiningService
    echo Display Name: Association Mining System Service
    echo.
    echo  FastAPI:  http://localhost:8080
    echo  Flask UI: http://localhost:5000
    echo  API Docs: http://localhost:8080/docs
    echo.
    echo View logs: logs\service.log
    echo.
) else (
    echo.
    echo ========================================
    echo Service Not Found
    echo ========================================
    echo.
    echo The service is not installed
    echo To install: install_service.bat
    echo.
)

pause
