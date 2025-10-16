#!/bin/bash

# Association Mining System - Production Startup Script

echo "Starting Association Mining System..."

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "Error: Python is not installed or not in PATH"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Copying from .env.production"
    cp .env.production .env
fi

# Install dependencies if requirements.txt is newer than last install
if [ requirements.txt -nt .install_timestamp ] || [ ! -f .install_timestamp ]; then
    echo "Installing/updating dependencies..."
    pip install -r requirements.txt
    touch .install_timestamp
fi

# Start API server in background
echo "Starting FastAPI server on port 8001..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 &
API_PID=$!

# Wait for API to start
sleep 5

# Start Flask UI server
echo "Starting Flask UI server on port 5000..."
python flask_ui_enhanced.py &
UI_PID=$!

# Create PID file for management
echo $API_PID > api.pid
echo $UI_PID > ui.pid

echo "Association Mining System started successfully!"
echo "API Server PID: $API_PID"
echo "UI Server PID: $UI_PID"
echo ""
echo "Access the application at:"
echo "  UI: http://localhost:5000"
echo "  API: http://localhost:8001"
echo ""
echo "To stop the system, run: ./stop.sh"

# Wait for any process to exit
wait