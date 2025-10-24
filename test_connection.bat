@echo off
REM Quick test to verify SSH tunnel and database connection

echo Testing database connection through SSH tunnel...
echo.

python -c "import mysql.connector; conn = mysql.connector.connect(host='localhost', port=6033, user='root', password='Falcon@WCS@123', database='neo', connect_timeout=5); print('SUCCESS! Connected to MySQL through SSH tunnel'); print('MySQL version:', conn.get_server_info()); conn.close()"

if %errorlevel% equ 0 (
    echo.
    echo ============================================================
    echo SUCCESS! Database connection working!
    echo You can now start the application with: start.bat
    echo ============================================================
) else (
    echo.
    echo ============================================================
    echo FAILED! Could not connect to database
    echo Make sure:
    echo 1. SSH tunnel is running
    echo 2. Credentials are correct
    echo ============================================================
)

echo.
pause
