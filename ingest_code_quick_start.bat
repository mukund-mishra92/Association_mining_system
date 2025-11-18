@echo off
REM Quick Start: Ingest NEO C# Codebase
echo.
echo ===============================================================================
echo   NEO CODE INGESTION - Quick Start
echo ===============================================================================
echo.

REM Activate virtual environment
echo [1/3] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [2/3] Starting code ingestion...
echo This will embed the NEO Fleet Manager C# codebase
echo Expected time: 5-10 minutes
echo.

python ingest_neo_code.py

echo.
echo [3/3] Verifying ingestion...
echo.

python check_vector_store.py

echo.
echo ===============================================================================
echo.
echo ✅ COMPLETE!
echo.
echo 💡 Next Steps:
echo    1. Start the chatbot: python app/main.py
echo    2. Ask code-related questions
echo    3. Examples:
echo       - "Show me the WarehouseController implementation"
echo       - "How is bin allocation coded?"
echo       - "What methods are in InventoryService?"
echo.
echo ===============================================================================
echo.

pause
