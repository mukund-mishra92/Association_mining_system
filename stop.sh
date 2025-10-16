#!/bin/bash

# Association Mining System - Stop Script

echo "Stopping Association Mining System..."

# Function to kill process by PID file
kill_by_pid_file() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null; then
            echo "Stopping $service_name (PID: $pid)..."
            kill $pid
            sleep 2
            if ps -p $pid > /dev/null; then
                echo "Force stopping $service_name..."
                kill -9 $pid
            fi
        fi
        rm -f "$pid_file"
    fi
}

# Stop services
kill_by_pid_file "api.pid" "FastAPI Server"
kill_by_pid_file "ui.pid" "Flask UI Server"

# Also kill any remaining processes by name
pkill -f "uvicorn app.main:app"
pkill -f "flask_ui_enhanced.py"

echo "Association Mining System stopped."