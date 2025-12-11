# Windows Service Setup Guide

This guide explains how to run the Association Mining System as a Windows Service that starts automatically in the background.

## What is a Windows Service?

A Windows Service runs in the background without requiring you to keep a command window open. It can:
- Start automatically when Windows boots
- Run without any user logged in
- Be managed through Windows Services Manager (`services.msc`)
- Keep running even if you close all windows

## Prerequisites

- **Windows OS** (Service functionality is Windows-specific)
- **Administrator Rights** (Required to install/manage services)
- **Python Virtual Environment** (venv folder should exist)
- **pywin32 Package** (Will be installed automatically)

## Quick Setup

### Option 1: Automated Setup (Recommended)

Run this script as Administrator:
```batch
scripts\service\setup_service.bat
```

This will:
1. Check prerequisites (Python, venv, admin rights)
2. Install required packages including pywin32
3. Install the Windows service
4. Optionally configure auto-start
5. Optionally start the service immediately

### Option 2: Manual Setup

1. **Install the Service** (Run as Administrator):
   ```batch
   scripts\service\install_service.bat
   ```

2. **Start the Service** (Run as Administrator):
   ```batch
   scripts\service\start_service.bat
   ```

## Service Management Scripts

All scripts in `scripts/service/` folder:

| Script | Purpose | Admin Required |
|--------|---------|----------------|
| `setup_service.bat` | Complete automated setup | ✓ Yes |
| `install_service.bat` | Install the service | ✓ Yes |
| `start_service.bat` | Start the service | ✓ Yes |
| `stop_service.bat` | Stop the service | ✓ Yes |
| `uninstall_service.bat` | Remove the service | ✓ Yes |
| `check_service.bat` | Check service status | No |

## Service Details

- **Service Name**: `AssociationMiningService`
- **Display Name**: Association Mining System Service
- **Description**: Runs the Association Mining System FastAPI server and scheduler in background
- **Log File**: `logs\service.log`

## Access Points (When Service is Running)

- **Flask UI**: http://localhost:5000
- **FastAPI**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs

## Configuration

### Auto-Start with Windows

To configure the service to start automatically when Windows boots:

**Option A**: During setup (when prompted by `setup_service.bat`)

**Option B**: Using Windows Services Manager
1. Press `Win + R`
2. Type `services.msc` and press Enter
3. Find "Association Mining System Service"
4. Right-click → Properties
5. Set Startup type to "Automatic"
6. Click OK

**Option C**: Using Command Line (as Administrator)
```batch
sc config AssociationMiningService start= auto
```

## Troubleshooting

### Service Won't Start

1. **Check if ports are in use**:
   ```powershell
   netstat -ano | findstr "8080"
   netstat -ano | findstr "5000"
   ```
   
2. **Check service logs**:
   ```batch
   type logs\service.log
   ```

3. **Verify service status**:
   ```batch
   scripts\service\check_service.bat
   ```
   Or use Windows Services Manager (`services.msc`)

### Installation Fails

1. **Ensure running as Administrator**
   - Right-click script → "Run as administrator"

2. **Check if pywin32 is installed**:
   ```batch
   venv\Scripts\python.exe -c "import win32serviceutil"
   ```

3. **Reinstall pywin32**:
   ```batch
   venv\Scripts\pip.exe install --force-reinstall pywin32
   venv\Scripts\python.exe -m pywin32_postinstall -install
   ```

### Service Installed but Not Working

1. **Uninstall and reinstall**:
   ```batch
   scripts\service\uninstall_service.bat
   scripts\service\install_service.bat
   ```

2. **Check Windows Event Viewer**:
   - Press `Win + R`
   - Type `eventvwr.msc`
   - Navigate to: Windows Logs → Application
   - Look for errors from "AssociationMiningService"

## Differences from Quick Start

| Feature | Quick Start (.bat) | Windows Service |
|---------|-------------------|-----------------|
| Command windows | Opens 2 windows | Runs hidden in background |
| Auto-start | Manual each time | Automatic on boot (if configured) |
| Requires login | Yes | No |
| Management | Close windows to stop | Use service scripts or services.msc |
| Logs | Console output | logs\service.log |

## Best Practices

1. **Development**: Use `quick_start.bat` for easier debugging (visible console output)
2. **Production/Demo**: Use Windows Service for hands-free operation
3. **Testing Changes**: Stop service, make changes, restart service
4. **Log Monitoring**: Regularly check `logs\service.log` for issues

## Uninstalling

To completely remove the Windows Service:

1. **Run uninstall script** (as Administrator):
   ```batch
   scripts\service\uninstall_service.bat
   ```

This will:
- Stop the service if running
- Remove the service from Windows
- Keep your data and configuration files intact

## Additional Commands

### Using Windows Services Manager

1. Press `Win + R`
2. Type `services.msc` and press Enter
3. Find "Association Mining System Service"
4. Right-click for options:
   - Start
   - Stop
   - Restart
   - Properties (configure startup type, recovery options)

### Using Command Line

```batch
# Check status
sc query AssociationMiningService

# Start service
net start AssociationMiningService

# Stop service
net stop AssociationMiningService

# Configure auto-start
sc config AssociationMiningService start= auto

# Configure manual start
sc config AssociationMiningService start= demand

# View service configuration
sc qc AssociationMiningService
```

## Notes

- The service uses the same `run_servers.py` script as `quick_start.bat`
- All application functionality remains the same
- Service runs with the same Python virtual environment
- Database connections and configurations are identical
- Stopping the service properly shuts down FastAPI and Flask servers

## Support

If you encounter issues:
1. Check `logs\service.log`
2. Check Windows Event Viewer (Application logs)
3. Try running `quick_start.bat` to verify the application works standalone
4. Ensure all prerequisites are met (Python, venv, admin rights)
