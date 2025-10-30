# 🚀 Association Mining Service Management

## The Right Way to Run and Test Services

### 🎯 **TERMINAL WORKFLOW**

#### **Terminal 1: Service Manager (Keep Open)**
```powershell
# Start all services and keep them running
py start_services.py
```
**⚠️ IMPORTANT:** 
- Keep this terminal open
- Don't run other commands here
- Services will stop if you close this terminal

#### **Terminal 2: Testing Terminal (Use for commands)**
```powershell
# Run tests while services are running
py test_mining.py

# Or check individual components
py -c "import requests; print(requests.get('http://localhost:5000').status_code)"
```

---

## 📋 **QUICK START GUIDE**

### 1️⃣ **Start Services (Terminal 1)**
```powershell
py start_services.py
```
Wait for:
```
✅ ALL SERVICES STARTED SUCCESSFULLY!
📍 Access Points:
   🌐 Web UI: http://localhost:5000
   🔧 API Docs: http://127.0.0.1:8001/docs
```

### 2️⃣ **Test Services (Terminal 2)**
```powershell
py test_mining.py
```
Choose from menu:
- `1` - Quick Test (7 days, 10 SKUs)
- `2` - Standard Test (30 days, 50 SKUs)
- `4` - Compare both methods

### 3️⃣ **Access Web UI**
Open browser: `http://localhost:5000`

---

## 🔧 **What Each Script Does**

### `start_services.py`
- ✅ Starts FastAPI server (port 8001)
- ✅ Starts Flask UI (port 5000)
- ✅ Tests all connections
- ✅ Keeps services running
- ✅ Shows access URLs

### `test_mining.py`
- 🧪 Tests Direct Mining
- 🧪 Tests API Mining
- 📊 Compares performance
- 🔍 Checks service status
- 📈 Shows progress tracking

### `flask_ui_enhanced.py`
- 🌐 Web interface
- 📊 Real-time progress
- 🛑 Cancel operations
- 📈 Results display

---

## ❌ **Common Mistakes to Avoid**

### **DON'T:**
- ❌ Run commands in the service terminal
- ❌ Close the service terminal
- ❌ Start services multiple times
- ❌ Use the same terminal for both

### **DO:**
- ✅ Use separate terminals
- ✅ Keep service terminal open
- ✅ Run tests in different terminal
- ✅ Check service status first

---

## 🆘 **Troubleshooting**

### **Services Won't Start**
```powershell
# Kill any existing processes
taskkill /F /IM python.exe /T
# Wait 5 seconds, then restart
py start_services.py
```

### **"Connection Refused" Errors**
1. Check if services are running: `py test_mining.py` → option 5
2. Restart services: Close Terminal 1, run `py start_services.py` again

### **Database Errors**
- Check MySQL is running
- Verify connection settings in `app/utils/config.py`

---

## 📊 **Testing Options**

| Test Type | Days Back | Top SKUs | Duration | Purpose |
|-----------|-----------|----------|----------|---------|
| Quick     | 7         | 10       | ~30s     | Fast check |
| Standard  | 30        | 50       | ~2min    | Full test |
| Custom    | Your choice | Your choice | Varies | Specific needs |

---

## 🎉 **Success Indicators**

When everything works:
```
✅ Flask UI: Working
✅ Database: Connected
✅ FastAPI: Connected
✅ Direct Mining: Generated X rules
✅ API Mining: Generated Y rules
🎉 ALL TESTS PASSED!
```

---

## 🔗 **Access Points**

- **Web UI:** http://localhost:5000
- **API Docs:** http://127.0.0.1:8001/docs
- **Health Check:** http://127.0.0.1:8001/api/v1/health
- **Connection Test:** http://localhost:5000/api/test-connection