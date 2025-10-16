@echo off
echo Starting Association Rule Mining Dashboard...
echo.
echo Make sure your FastAPI server is running on http://localhost:8000
echo If not, start it with: py -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
echo.
echo Opening Streamlit Dashboard...
streamlit run streamlit_ui.py --server.port 8501
pause