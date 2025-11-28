# Windows Service Setup - Two Options

## ⚠️ Current Issue
The pywin32-based Windows service is experiencing compatibility issues with the virtual environment. 

## ✅ **Recommended Solution: Use NSSM**

NSSM (Non-Sucking Service Manager) is a more reliable way to run Python scripts as Windows services.

### Steps to Install with NSSM:

1. **Download NSSM**
   - Go to https://nssm.cc/download
   - Download `nssm-2.24.zip`
   - Extract `nssm.exe` from the `win64` folder
   - Copy `nssm.exe` to this directory (`d:\ML_Deployments\Association_mining_system\`)

2. **Install the Service**
   ```powershell
   # Right-click and "Run as Administrator"
   .\install_service_nssm.bat
   ```

3. **Start the Service**
   ```powershell
   nssm start AssociationMiningService
   ```
   
   Or use the start script:
   ```powershell
   .\start_service.bat
   ```

4. **Verify Service is Running**
   ```powershell
   nssm status AssociationMiningService
   ```
   
   Check the servers:
   - FastAPI: http://localhost:8080/docs
   - Flask UI: http://localhost:5000

### NSSM Commands:

```powershell
# Start service
nssm start AssociationMiningService

# Stop service
nssm stop AssociationMiningService

# Restart service
nssm restart AssociationMiningService

# Check status
nssm status AssociationMiningService

# Remove service
nssm remove AssociationMiningService confirm
```

### Logs Location:
- Service runner: `logs\service_runner.log`
- FastAPI output: `logs\fastapi.log`
- Flask output: `logs\flask.log`
- NSSM stdout: `logs\service_stdout.log`
- NSSM stderr: `logs\service_stderr.log`

---

## 🔧 Alternative: Manual pywin32 Service (Advanced)

If you prefer to use the pywin32-based service and want to troubleshoot:

1. The service is already installed but has virtual environment path conflicts
2. Run in debug mode to see errors:
   ```powershell
   python windows_service.py debug
   ```

3. The main issues are:
   - sys.prefix conflicts with virtual environment
   - Subprocess execution context issues
   - Service startup timeout

---

## 🎯 Why NSSM is Better

✅ **No Python/venv conflicts** - Runs Python scripts directly  
✅ **Automatic restart** - If process dies, NSSM restarts it  
✅ **Better logging** - Separate stdout/stderr capture  
✅ **Easy management** - Simple command-line interface  
✅ **No timeout issues** - Handles long startup times  
✅ **Works with any executable** - Not just Python services  

The pywin32 approach requires complex service infrastructure that doesn't play well with virtual environments, while NSSM simply wraps your Python script and manages it as a service.
