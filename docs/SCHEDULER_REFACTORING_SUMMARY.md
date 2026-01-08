# Scheduler Refactoring - Feature Parity with Manual Mining API

## Overview
Refactored the association mining scheduler to use the same mining function and parameters as the manual API-based mining, ensuring feature parity and eliminating code duplication.

## Key Changes

### 1. Database Schema Updates
**File:** Database migrations via `add_enhanced_mining_columns.py`

**New Columns Added to `mining_schedules` table:**
- `max_items` (INT DEFAULT 200) - Number of top SKUs to analyze
- `min_item_frequency` (INT DEFAULT 5) - Minimum SKU frequency filter
- `days_back` (INT DEFAULT 365) - Historical data period in days
- `use_enhanced_mining` (BOOLEAN DEFAULT 1) - Enable time-weighted mining
- `time_weighting_method` (VARCHAR(50) DEFAULT 'exponential_decay') - Time weighting algorithm
- `time_segmentation` (VARCHAR(20) DEFAULT 'weekly') - Time period grouping

### 2. Scheduler Service Refactoring
**File:** `app/modules/association_mining/services/scheduler_service.py`

#### Changes to `_execute_mining_job_async()` (Line 376)
**Before:** 200+ lines of duplicated mining logic with hardcoded parameters
**After:** Calls shared `run_mining_task()` function from endpoints.py

**Key Improvements:**
- ✅ Eliminated code duplication
- ✅ Uses exact same mining logic as manual API
- ✅ Automatically inherits all mining enhancements
- ✅ Consistent behavior between scheduled and manual mining
- ✅ Created minimal task manager for scheduler context
- ✅ Maintained 10-minute timeout protection
- ✅ Proper job logging to mining_job_logs table

**Implementation Details:**
```python
# Created SchedulerTaskManager class for scheduler jobs
class SchedulerTaskManager:
    """Minimal task manager for scheduler jobs that logs to mining_job_logs"""
    def start_task(self, task_id, message): ...
    def update_progress(self, task_id, progress, message): ...
    def complete_task(self, task_id, result=None, message=""): ...
    def fail_task(self, task_id, error_msg): ...

# Temporarily replaces global task_manager during scheduled execution
# Calls run_mining_task() with all schedule parameters
# Restores original task_manager after completion
```

#### Changes to `create_schedule()` (Line 70)
**Added Parameters:**
- `days_back`: Historical data period (default: 365 days)
- `max_items`: Top SKUs to analyze (default: 200)
- `min_item_frequency`: Minimum SKU frequency (default: 5)
- `use_enhanced_mining`: Enable enhanced mining (default: True)
- `time_weighting_method`: Weighting algorithm (default: 'exponential_decay')
- `time_segmentation`: Time grouping (default: 'weekly')

**Updated INSERT query to include all new columns**

### 3. API Endpoint Models
**File:** `app/modules/association_mining/api/scheduler_endpoints.py`

#### Updated `ScheduleCreateRequest` Model (Line 12)
**Added Fields:**
```python
# Data filtering parameters
days_back: Optional[int] = Field(365, ge=1, le=3650)
max_items: Optional[int] = Field(200, ge=10, le=1000)
min_item_frequency: Optional[int] = Field(5, ge=1, le=100)

# Enhanced mining parameters
use_enhanced_mining: Optional[bool] = Field(True)
time_weighting_method: Optional[str] = Field("exponential_decay")
time_segmentation: Optional[str] = Field("weekly")
```

#### Updated `ScheduleUpdateRequest` Model
Added same fields as optional for schedule updates

### 4. UI Enhancements
**File:** `app/web/templates/association_mining.html`

#### Added Form Fields (Lines 617-668)
**New Input Controls:**

1. **Days Back** (Line 617)
   - Input: Number field (1-3650 days)
   - Default: 365 days
   - Description: "Historical data period in days"

2. **Enhanced Mining** (Line 625)
   - Input: Dropdown (Enabled/Disabled)
   - Default: Enabled
   - Description: "Use time-weighted mining"

3. **Time Segmentation** (Line 632)
   - Input: Dropdown (Weekly/Monthly/Daily)
   - Default: Weekly
   - Description: "Time period grouping"

4. **Time Weighting Method** (Line 645)
   - Input: Dropdown with 5 options:
     - Exponential Decay (default)
     - Linear Decay
     - Seasonal Patterns
     - Recency & Frequency
     - Trend Adaptive
   - Description: "Method for time-based weighting"

#### Updated JavaScript Functions

**`createSchedule()` Function (Line 1306):**
- Added `days_back` parameter extraction
- Added `use_enhanced_mining` parameter extraction
- Added `time_weighting_method` parameter extraction
- Added `time_segmentation` parameter extraction

**`resetScheduleForm()` Function (Line 1354):**
- Resets `scheduleDaysBack` to '365'
- Resets `scheduleEnhancedMining` to 'true'
- Resets `scheduleTimeWeighting` to 'exponential_decay'
- Resets `scheduleTimeSegmentation` to 'weekly'

## Benefits

### 1. Code Reuse
- **Before:** 200+ lines of duplicated mining logic in scheduler
- **After:** Single shared function used by both scheduler and manual API
- **Impact:** Easier maintenance, single source of truth

### 2. Feature Parity
- **Before:** Scheduler had different capabilities than manual mining
- **After:** Scheduler has exact same features as manual mining
- **Impact:** Consistent user experience, same powerful features everywhere

### 3. Automatic Enhancement Inheritance
- **Before:** Changes to mining logic required updating both scheduler and API
- **After:** Changes to `run_mining_task()` automatically apply to scheduler
- **Impact:** Future enhancements work everywhere automatically

### 4. Parameter Flexibility
- **Before:** Hardcoded values (max_items=200, min_item_frequency=5)
- **After:** User-configurable via UI form
- **Impact:** Users can optimize for their specific needs

### 5. Enhanced Mining Capabilities
- **New:** Time-weighted mining in scheduler
- **New:** Multiple time weighting algorithms
- **New:** Configurable time segmentation
- **New:** Historical data period control
- **Impact:** More sophisticated scheduled analysis

## Time Weighting Methods Available

1. **Exponential Decay** (default)
   - Recent data weighted more heavily
   - Smooth decay over time
   - Best for: Fast-changing trends

2. **Linear Decay**
   - Constant rate of decay
   - Simple and predictable
   - Best for: Steady trends

3. **Seasonal Patterns**
   - Weights based on seasonal cycles
   - Identifies recurring patterns
   - Best for: Products with seasons

4. **Recency & Frequency**
   - Balances recent transactions with overall frequency
   - Considers both timing and volume
   - Best for: General recommendations

5. **Trend Adaptive**
   - Automatically adjusts to data trends
   - Dynamic weighting
   - Best for: Complex patterns

## Testing Recommendations

### Test Case 1: Basic Schedule with Defaults
- Create schedule with default parameters
- Verify it executes successfully
- Check mining_job_logs for results

### Test Case 2: Custom Parameters
- Create schedule with:
  - days_back: 180 (6 months)
  - max_items: 100 (top 100 SKUs)
  - min_item_frequency: 10 (strict filtering)
  - use_enhanced_mining: true
  - time_weighting_method: seasonal_patterns
  - time_segmentation: monthly
- Verify custom parameters are stored
- Check execution uses these parameters

### Test Case 3: Timeout Protection
- Create schedule with very low min_support (e.g., 0.001)
- Verify job times out after 10 minutes
- Check job marked as failed in mining_job_logs

### Test Case 4: Error Handling
- Create schedule with invalid parameters
- Verify proper error messages
- Check database rollback works

## Migration Notes

### For Existing Schedules
- Old schedules will use default values for new columns
- No manual migration required
- Existing schedules continue to work

### For New Schedules
- All new parameters available immediately
- UI pre-filled with sensible defaults
- Users can customize as needed

## Architecture Improvements

### Before
```
Manual API Mining ──► run_mining_task() ──► CleanAssociationMiningService
                                              
Scheduled Mining ──► _execute_mining_job_async() ──► CleanAssociationMiningService
                     (200+ lines of duplicated logic)
```

### After
```
Manual API Mining ────┐
                      ├──► run_mining_task() ──► CleanAssociationMiningService
Scheduled Mining ─────┘
                (shared function, single source of truth)
```

## Files Modified

1. ✅ `add_enhanced_mining_columns.py` - Database migration script
2. ✅ `app/modules/association_mining/services/scheduler_service.py` - Scheduler refactoring
3. ✅ `app/modules/association_mining/api/scheduler_endpoints.py` - API models
4. ✅ `app/web/templates/association_mining.html` - UI form enhancements

## Next Steps

1. **Testing:** Create test schedules with various parameter combinations
2. **Documentation:** Update user documentation with new features
3. **Monitoring:** Watch job execution logs for any issues
4. **Optimization:** Gather feedback on default values
5. **Training:** Educate users on new parameters

## Success Criteria

✅ Scheduler uses shared `run_mining_task()` function  
✅ Database schema includes all new columns  
✅ API endpoints accept new parameters  
✅ UI form exposes all new parameters  
✅ Form JavaScript sends all parameters  
✅ Default values match manual API defaults  
✅ Code duplication eliminated  
✅ Timeout protection maintained  
✅ Error handling preserved  

## Known Limitations

1. **Manual Testing Required:** Automated tests not yet created
2. **No Update UI:** Schedule update form not yet enhanced (only creation form updated)
3. **No Validation Rules:** Parameter interdependencies not validated (e.g., max_items vs min_item_frequency)

## Future Enhancements

1. Add schedule update form with new parameters
2. Add parameter validation (e.g., warn if max_items too low with min_item_frequency too high)
3. Add parameter presets (e.g., "Fast", "Balanced", "Comprehensive")
4. Add schedule templates
5. Add parameter recommendations based on data size
6. Add execution time estimation based on parameters

---

**Completed:** January 2025  
**Author:** GitHub Copilot  
**Status:** Ready for testing
