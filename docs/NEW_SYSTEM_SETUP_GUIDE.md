# 🏗️ NEW SYSTEM SETUP GUIDE

## 🎯 **For a NEW SYSTEM, follow this order:**

### 1️⃣ **FIRST - Setup & Dependencies**
```bash
# Run this FIRST on a new system:
scripts\setup.bat
```

**What it does:**
- ✅ Installs Python dependencies (`pip install -r requirements.txt`)
- ✅ Shows configuration information
- ✅ Prepares the environment

### 2️⃣ **SECOND - Configuration**
```bash
# Copy and configure environment:
copy .env.example .env
```

**Then edit `.env` file with your database settings:**
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=neo
```

### 3️⃣ **THIRD - Database Setup**
```bash
# Create required tables:
python utils/setup/create_scheduler_tables.py
python utils/setup/create_recommendations_table.py
```

### 4️⃣ **FOURTH - Start the System**
```bash
# For new system with dependency check:
start_system.bat

# OR for quick start (if deps already installed):
quick_start.bat
```

## 📋 **COMPLETE NEW SYSTEM CHECKLIST:**

### ✅ **Prerequisites:**
- [ ] Python 3.8+ installed
- [ ] MySQL server running
- [ ] Git (if cloning from repository)

### ✅ **Setup Steps:**
1. [ ] Clone/download the project
2. [ ] Run `scripts\setup.bat` (install dependencies)
3. [ ] Copy `.env.example` to `.env`
4. [ ] Edit `.env` with your database settings
5. [ ] Run database setup scripts
6. [ ] Start with `start_system.bat`

### ✅ **Verification:**
- [ ] Web UI loads at http://localhost:5000
- [ ] API works at http://localhost:8080
- [ ] Database connection test passes
- [ ] Can run mining operations

## 🚨 **CURRENT ISSUE - NEED TO FIX:**

Both `start_system.bat` and other scripts reference `flask_ui_enhanced.py` which was deleted.

**All startup scripts need to be updated to use:**
```bash
app/web/main.py
```

## 🎯 **RECOMMENDATION FOR NEW SYSTEMS:**

**Use this sequence:**
1. `scripts\setup.bat` - Install dependencies
2. Configure `.env` file
3. Setup database tables  
4. `start_system.bat` (after we fix it)

**This ensures everything is properly installed and configured!**