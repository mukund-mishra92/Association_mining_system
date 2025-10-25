@echo off
echo ================================
echo Association Rule Mining API Setup
echo ================================

echo.
echo 1. Installing Python dependencies...
py -m pip install -r requirements.txt

echo.
echo 2. Current configuration:
echo Database Host: %DB_HOST%
echo Database Name: %DB_NAME%
echo.

echo 3. Configuration files:
echo - Main config: .env
echo - Source tables: ORDER_TABLE, SKU_MASTER_TABLE
echo - Output table: RECOMMENDATIONS_TABLE
echo.

echo Available time weighting methods:
echo - exponential_decay (default)
echo - linear_decay
echo - seasonal_patterns
echo - recency_frequency  
echo - trend_adaptive
echo.

echo Available time segmentation:
echo - weekly (default)
echo - monthly
echo - daily
echo.

echo 4. To start the API server:
echo uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
echo.

echo 5. To test the API:
echo python test_api.py
echo.

echo 6. API endpoints will be available at:
echo - Health check: http://localhost:8000/api/v1/health
echo - Start mining: POST http://localhost:8000/api/v1/mine-rules
echo - Get recommendations: GET http://localhost:8000/api/v1/recommendations/{item_name}
echo - API docs: http://localhost:8000/docs
echo.

echo ================================
echo Setup complete! 
echo ================================
pause