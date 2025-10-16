# Windows Python Command Reference

## Python Command Compatibility

Windows systems may have different Python commands available:

### Option 1: Python Launcher (`py` command)
```cmd
py --version
py -m pip install package_name
py script.py
```

### Option 2: Direct Python (`python` command)  
```cmd
python --version
python -m pip install package_name
python script.py
```

### Option 3: Python3 (`python3` command)
```cmd
python3 --version
python3 -m pip install package_name
python3 script.py
```

## Startup Scripts Available

### 1. **start.bat** (Uses `py` command)
- Optimized for Windows Python Launcher
- Best for most Windows 10/11 systems
- Uses `py` command throughout

### 2. **start_compatible.bat** (Auto-detects)
- Tries `py` first, falls back to `python`
- Maximum compatibility
- Recommended for shared environments

### 3. **Manual Commands** (Your system uses `py`)
```cmd
# Navigate to project
cd c:\Users\Balmukund.Mishra\Desktop\NEO\association_mining_system

# Install dependencies
py -m pip install -r requirements.txt

# Terminal 1: Start API
py -m uvicorn app.main:app --host 0.0.0.0 --port 8001

# Terminal 2: Start UI  
py flask_ui_enhanced.py
```

## Quick Test Your Python Command

```cmd
# Test which command works on your system
py --version
python --version
python3 --version
```

Use whichever command returns a version number successfully.