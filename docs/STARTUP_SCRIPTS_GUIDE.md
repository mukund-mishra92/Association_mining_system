# 🚀 STARTUP SCRIPTS GUIDE

## 🎯 **For NEW SYSTEM Setup:**

### 📋 **Complete Setup Sequence:**
```bash
# 1. FIRST - Install dependencies
scripts\setup.bat

# 2. SECOND - Configure environment  
copy .env.example .env
# Edit .env with your database settings

# 3. THIRD - Setup database
python utils/setup/create_scheduler_tables.py
python utils/setup/create_recommendations_table.py

# 4. FOURTH - Start the system
start_system.bat
```

---

## 🎯 **For EXISTING SYSTEM (already configured):**

### ⚡ **Quick Options:**

#### Option 1: Full System Start
```bash
start_system.bat
```
- ✅ Comprehensive startup
- ✅ Database config UI + FastAPI backend
- ✅ Best for development and configuration

#### Option 2: Quick Start  
```bash
quick_start.bat
```
- ✅ Fast startup
- ✅ Skip dependency checks
- ✅ Best for daily use

#### Option 3: Basic Start
```bash
start.bat
```
- ✅ Standard startup
- ✅ Includes dependency checks
- ✅ Good middle ground

---

## 📊 **Script Comparison:**

| Script | Purpose | When to Use | Features |
|--------|---------|-------------|----------|
| `scripts\setup.bat` | 🔧 Setup | NEW system only | Installs dependencies |
| `start_system.bat` | 🏗️ Full startup | NEW system / Development | Complete setup + UI |
| `start.bat` | 🔄 Standard start | Daily use | Dependency check + start |
| `quick_start.bat` | ⚡ Quick start | Quick testing | Skip checks, fast start |

---

## ✅ **RECOMMENDED APPROACH:**

### 🆕 **For Brand New System:**
```bash
1. scripts\setup.bat
2. Configure .env file
3. Setup database tables
4. start_system.bat
```

### 🔄 **For Daily Use:**
```bash
quick_start.bat
```

### 🐛 **For Development/Debugging:**
```bash
start_system.bat
```

---

## 🎯 **Access Points:**
- **Web UI:** http://localhost:5000
- **FastAPI:** http://localhost:8080 (or 8001 for start_system.bat)
- **API Docs:** http://localhost:8080/docs

All scripts have been **FIXED** to use the correct Flask path: `app/web/main.py` ✅