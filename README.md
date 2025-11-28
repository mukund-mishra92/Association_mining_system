<<<<<<< HEAD
# Association Mining System 🔗

A comprehensive data mining platform for analyzing customer purchase patterns and SKU performance. Built with Flask, FastAPI, and MySQL.

## ✨ New Features

� **Windows Service Support** - Run the system as a background Windows service with auto-restart capabilities  
🔑 **Primary Keys on All Tables** - Enhanced database integrity with proper primary keys on all tables  
📊 **Scheduler Service** - Automated mining jobs with configurable schedules  
🔄 **Auto-Recovery** - Automatic process restart on failures  

**📖 See [SERVICE_SETUP.md](SERVICE_SETUP.md) for complete setup instructions**
# Association Mining System — Quick Commands

Minimal, one-liners to set up and run on Windows PowerShell.

## Setup (first time)
- Create venv: `python -m venv .venv`
- Activate venv: `.\\.venv\\Scripts\\Activate.ps1`
- Install deps: `pip install --upgrade pip; pip install -r requirements.txt`
- Create env (if missing): `Copy-Item .env.example .env` (then edit DB settings)

## Run (development)
- Start both servers (bg): `.\\quick_start.bat` — FastAPI:8080 + Flask:5000
- Stop both servers: `.\\stop_servers.bat`
- Start via Python: `python .\\run_servers.py start` — Starts both
- Stop via Python: `python .\\run_servers.py stop` — Stops both

## Windows Service (Admin)
- Install service: `.\\scripts\\service\\install_service.bat` — Registers Windows service
- Start service: `.\\scripts\\service\\start_service.bat` — Runs in background
- Stop service: `.\\scripts\\service\\stop_service.bat` — Stops the service
- Check status: `.\\scripts\\service\\check_service.bat` — Shows status
- Uninstall: `.\\scripts\\service\\uninstall_service.bat` — Removes service

## URLs
- UI: http://localhost:5000
- API: http://localhost:8080
- Docs: http://localhost:8080/docs

## Logs
- Folder: `logs\\` — Service and server logs

## Notes
- DB and table names come from `.env` or the UI Database Config.
- If ports conflict, update `BASE_URL`/`API_BASE` in `app/web/main.py` and `.env`.
