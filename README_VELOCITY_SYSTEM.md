# 🚀 QUICK START GUIDE - How to Run the Velocity Analysis System

## 📋 **TL;DR - Fastest Way to Run**

### **Option 1: Double-click Batch File (Easiest)**
```
1. Navigate to: C:\Users\Balmukund.Mishra\Desktop\NEO\association_mining_system
2. Double-click: run_velocity_system.bat
3. Wait for completion (about 1-2 minutes)
4. ✅ Done!
```

### **Option 2: Command Line (Recommended)**
```bash
# Navigate to project directory
cd C:\Users\Balmukund.Mishra\Desktop\NEO\association_mining_system

# Activate virtual environment
.\venv\Scripts\activate

# Run complete analysis
python run_velocity_analysis.py

# OR run only SKU velocity analysis
python run_velocity_analysis.py --sku-only

# OR run only system check
python run_velocity_analysis.py --check-only
```

---

## 📊 **What the System Does**

✅ **Analyzes 609 SKUs** with sufficient order history (≥5 orders in 90 days)
✅ **Calculates velocity scores** using time-decay weighted algorithm
✅ **Updates sku_master table** with velocity classifications:
   - 🔴 **High Velocity (3)**: ~122 SKUs (20%)
   - 🟡 **Medium Velocity (2)**: ~183 SKUs (30%)  
   - 🟢 **Low Velocity (1)**: ~304 SKUs (50%)
✅ **Tracks changes** in sku_velocity_history table
✅ **Completes in ~1 second** for current dataset

---

## 🎯 **Expected Output**

```
============================================================
🚀 VELOCITY ANALYSIS SYSTEM
============================================================
🕐 Started at: 2025-11-04 16:00:14

✅ Configuration loaded successfully
✅ Database connection established  
✅ sku_master: 406,078 records
✅ wms_to_wcs_order_line_request_data: 154,856 records

✅ SKU velocity analysis completed in 1.05 seconds
   📊 Total SKUs Updated: 609
   📊 Total SKUs Analyzed: 609
   🔴 High Velocity (3): 122 SKUs (20.0%)
   🟡 Medium Velocity (2): 183 SKUs (30.0%) 
   🟢 Low Velocity (1): 304 SKUs (49.9%)

✅ All velocity analysis operations completed successfully!
ℹ️  The system is ready for production use.
🕐 Completed at: 2025-11-04 16:00:17
```

---

## ⚙️ **Configuration**

Current velocity calculation parameters:
- **Analysis Period**: 90 days (3 months of order history)
- **Minimum Orders**: 5 orders required to qualify for analysis
- **Time Decay Rate**: 5% per day (recent orders weighted higher)
- **High Velocity Threshold**: 80th percentile of weighted scores
- **Medium Velocity Threshold**: 50th percentile of weighted scores

---

## 🔄 **Scheduling for Production**

### **Option 1: Windows Task Scheduler (Recommended)**
1. Open Task Scheduler
2. Create Basic Task → "Weekly Velocity Analysis"
3. Trigger: Weekly, Monday 9:00 AM
4. Action: Start a program
   - Program: `C:\Users\Balmukund.Mishra\Desktop\NEO\association_mining_system\run_velocity_system.bat`
5. ✅ Done! Automatic weekly execution

### **Option 2: Manual Execution**
Run whenever needed using the batch file or command line.

---

## 📈 **Results Verification**

After running, verify results in your database:

```sql
-- Check velocity distribution
SELECT VELOCITY, COUNT(*) as count 
FROM sku_master 
WHERE VELOCITY IS NOT NULL 
GROUP BY VELOCITY 
ORDER BY VELOCITY DESC;

-- Check recent updates
SELECT COUNT(*) as recent_changes
FROM sku_velocity_history 
WHERE changed_at >= DATE_SUB(NOW(), INTERVAL 1 DAY);
```

---

## 🚨 **Troubleshooting**

### **Problem: Database Connection Error**
```
❌ Can't connect to MySQL server
```
**Solution:** Ensure MySQL is running and check database credentials in config.

### **Problem: No SKUs Processed**
```
❌ No SKUs meet minimum order criteria
```
**Solution:** Check if order data exists in `wms_to_wcs_order_line_request_data` table.

### **Problem: Import Errors**
```
❌ Import Error: No module named 'app'
```
**Solution:** Ensure you're running from the project root directory and virtual environment is activated.

---

## 🎯 **System Files Created**

The velocity analysis system includes these key files:

- **`run_velocity_analysis.py`** - Main execution script
- **`run_velocity_system.bat`** - Windows batch launcher  
- **`VELOCITY_SYSTEM_SETUP_GUIDE.md`** - Detailed setup guide
- **`app/modules/velocity_analysis/`** - Core velocity analysis modules
- **`quick_velocity_test.py`** - Comprehensive test script
- **`debug_*.py`** - Various debugging utilities

---

## 📞 **System Status**

✅ **PRODUCTION READY**
- All database triggers fixed
- Data type conversion issues resolved
- Table structure mismatches corrected
- SKU velocity calculation working perfectly
- 609 SKUs successfully processed
- Performance optimized (1 second execution)
- Error handling implemented
- Comprehensive logging included

---

## 🎉 **Next Steps**

1. **Run the system** using the instructions above
2. **Verify results** in your database
3. **Set up scheduling** for automated execution
4. **Monitor performance** and adjust parameters if needed
5. **Integrate with existing workflows** as required

**Your velocity analysis system is ready for production use!** 🚀