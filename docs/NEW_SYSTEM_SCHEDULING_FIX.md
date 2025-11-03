# 🚀 NEW SYSTEM SETUP GUIDE

## ❓ **Problem:** 
After pulling code from GitHub to a new system, you can't create or save schedules.

## 🎯 **Root Cause:**
GitHub only transfers **code files**, not **database tables**. The new system needs database setup.

---

## 📋 **COMPLETE SETUP FOR NEW SYSTEM:**

### 1️⃣ **Prerequisites on New System:**
```bash
✅ Python 3.8+ installed
✅ MySQL Server running  
✅ Git (for cloning repository)
```

### 2️⃣ **Step-by-Step Setup:**

#### **A. Clone Repository:**
```bash
git clone https://github.com/mukund-mishra92/Association_mining_system.git
cd Association_mining_system
```

#### **B. Install Dependencies:**
```bash
# Run setup script
scripts\setup.bat

# OR manually:
pip install -r requirements.txt
```

#### **C. Configure Environment:**
```bash
# Copy environment template
copy .env.example .env

# Edit .env with your database settings:
DB_HOST=localhost
DB_PORT=3306  
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=neo
```

#### **D. Setup Database (CRITICAL STEP):**
```bash
# This is the KEY step that fixes scheduling issues:
python utils/setup/new_system_setup.py
```

#### **E. Start Application:**
```bash
# Full system start
start_system.bat

# OR quick start
quick_start.bat
```

### 3️⃣ **Verification:**
- ✅ Web UI loads: http://localhost:5000
- ✅ Can create new schedules
- ✅ Can save schedule configurations
- ✅ Schedules appear in the list

---

## 🔧 **What the Database Setup Script Does:**

### **Creates Required Tables:**
1. **`mining_schedules`** - Stores schedule configurations
2. **`mining_schedule_stats`** - Tracks schedule performance
3. **`mining_job_logs`** - Logs mining job execution
4. **`my_recommendation`** - Stores recommendation results
5. **`sku_recommendations`** - Stores SKU-based recommendations

### **Verifies Functionality:**
- ✅ Tests table creation
- ✅ Validates insert/delete operations
- ✅ Confirms scheduler functionality

---

## 🚨 **TROUBLESHOOTING:**

### **Issue: "Can't create/save schedules"**
**Solution:** Run the database setup script:
```bash
python utils/setup/new_system_setup.py
```

### **Issue: "Database connection failed"**
**Solutions:**
1. Start MySQL service: `net start MySQL80`
2. Check .env file configuration
3. Verify MySQL credentials
4. Create database: `CREATE DATABASE neo;`

### **Issue: "Tables already exist but scheduling not working"**
**Solution:** Check table structure compatibility:
```bash
python utils/analysis/recommendation_validator.py
```

---

## 📁 **NEW SYSTEM CHECKLIST:**

### ✅ **On Source System (Your Current):**
- [x] Code working properly
- [x] Push to GitHub: `git push origin main`

### ✅ **On Target System (New Machine):**
- [ ] Clone repository
- [ ] Install dependencies (`scripts\setup.bat`)
- [ ] Configure `.env` file
- [ ] **RUN DATABASE SETUP:** `python utils/setup/new_system_setup.py`
- [ ] Start application (`start_system.bat`)
- [ ] Test scheduling functionality

---

## 🎯 **KEY INSIGHT:**

The scheduling issue happens because:
- **GitHub transfers:** Code, configuration templates, documentation
- **GitHub does NOT transfer:** Database tables, data, local environment settings

**The solution:** Run the database setup script on every new system!

---

## 📞 **Quick Fix for Your Other System:**

```bash
# 1. Navigate to project directory
cd path/to/Association_mining_system

# 2. Setup database tables (THE CRITICAL STEP)
python utils/setup/new_system_setup.py

# 3. Start application
start_system.bat
```

**That's it!** Your scheduling functionality will work immediately. 🎉