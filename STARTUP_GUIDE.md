# Association Mining System - Startup Scripts

## Quick Reference

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `setup_and_start.bat` | Full setup + start | **First time** on a new system |
| `quick_start.bat` | Start servers only | **Daily use** on configured system |
| `stop_servers.bat` | Stop all servers | When you want to stop the system |

---

## For New Systems: setup_and_start.bat

### What it does:
1. ✅ Checks Python installation
2. ✅ Creates virtual environment
3. ✅ Installs all dependencies
4. ✅ Checks .env configuration
5. ✅ Runs database migrations (optional)
6. ✅ Starts both servers

### Usage:
```bash
# Double-click the file, or run from command line:
setup_and_start.bat
```

### Prerequisites:
- Python 3.10 or higher installed
- `.env` file with database configuration

### First-time Setup Checklist:
1. Install Python from [python.org](https://python.org)
2. Clone/download this repository
3. Create `.env` file (see configuration below)
4. Run `setup_and_start.bat`
5. Access UI at http://localhost:5000

---

## For Daily Use: quick_start.bat

### What it does:
1. ✅ Validates virtual environment exists
2. ✅ Validates .env configuration exists
3. ✅ Starts both servers

### Usage:
```bash
# Double-click the file, or run from command line:
quick_start.bat
```

### When it works:
- After initial setup is complete
- When you've already run `setup_and_start.bat` once
- For regular daily startups

---

## Stopping Servers: stop_servers.bat

### What it does:
- Stops FastAPI server (port 8080)
- Stops Flask UI server (port 5000)

### Usage:
```bash
# Double-click the file, or run from command line:
stop_servers.bat
```

### Alternative methods:
- Close the command windows directly
- Press Ctrl+C in each server window

---

## Configuration: .env File

Create a `.env` file in the root directory with:

```env
# Database Configuration
DB_HOST=your_database_host
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_NAME=your_database_name
DB_PORT=3306

# Database Tables
ORDER_TABLE=wms_to_wcs_order_line_request_data
SKU_MASTER_TABLE=sku_master
RECOMMENDATIONS_TABLE=sku_recommendations

# Mining Parameters
MIN_SUPPORT=0.05
MIN_CONFIDENCE=0.25
MIN_LIFT=1.0
MAX_RECOMMENDATIONS=10

# Data Filtering
MAX_ITEMS=400
MIN_ITEM_FREQUENCY=5

# Temporal Analysis
DECAY_RATE=0.1
RECENCY_WEIGHT=0.3
```

---

## Server URLs

After starting:

| Service | URL | Description |
|---------|-----|-------------|
| Flask UI | http://localhost:5000 | Web interface for mining |
| FastAPI | http://localhost:8080 | REST API backend |
| API Docs | http://localhost:8080/docs | Interactive API documentation |

---

## Troubleshooting

### "Python not found"
- Install Python 3.10+ from python.org
- During installation, check "Add Python to PATH"
- Restart command prompt after installation

### "Virtual environment not found"
- Run `setup_and_start.bat` for first-time setup
- Don't run `quick_start.bat` on a new system

### ".env file not found"
- Create `.env` file in root directory
- Copy settings from Configuration section above
- Update with your database credentials

### "Failed to install dependencies"
- Check internet connection
- Try running: `pip install --upgrade pip`
- Manually install: `pip install -r requirements.txt`

### "Database connection failed"
- Verify database is running
- Check credentials in `.env` file
- Ensure database server is accessible
- Check firewall settings

### Servers won't start
- Check if ports 5000 and 8080 are available
- Close any existing instances
- Run `stop_servers.bat` first
- Try again with `quick_start.bat`

---

## Development Notes

### Manual Start (Development):
```bash
# Activate virtual environment
venv\Scripts\activate.bat

# Start FastAPI (Terminal 1)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Start Flask UI (Terminal 2)
python app\web\main.py
```

### Running Migrations:
```bash
venv\Scripts\activate.bat
python migrate_scheduler_tables.py
```

### Testing Installation:
```bash
venv\Scripts\activate.bat
python -c "import mlxtend; import pymysql; print('All imports OK!')"
```

---

## Scripts Removed

The following redundant scripts have been removed:
- ~~start.bat~~
- ~~start_system.bat~~
- ~~scripts/setup.bat~~
- ~~scripts/stop.bat~~
- ~~scripts/start_compatible.bat~~
- ~~scripts/run_ui.bat~~

Use the three main scripts instead:
- `setup_and_start.bat` (new systems)
- `quick_start.bat` (daily use)
- `stop_servers.bat` (shutdown)
