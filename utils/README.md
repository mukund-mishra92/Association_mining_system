# Utils Directory

This directory contains utility scripts organized by function.

## 📁 Directory Structure

### 🔍 analysis/
Scripts for analyzing system behavior and performance:
- `analyze_recommendation_behavior.py` - Analyzes how recommendations are handled (replace vs accumulate)

### 🗄️ database/
Database utilities and diagnostic scripts:
- `check_actual_data.py` - Verifies actual data in database tables
- `check_join.py` - Checks database join operations
- `check_recommendations.py` - Validates recommendation data
- `check_recommendations_table.py` - Checks recommendation table structure
- `check_table.py` - General table validation utility
- `diagnose_data.py` - Comprehensive data diagnostics

### 🐛 debugging/
Debugging and logging utilities:
- `check_logs.py` - Log file analysis and debugging

### 🛠️ setup/
Setup and initialization scripts:
- `create_recommendations_table.py` - Creates recommendation tables
- `create_scheduler_tables.py` - Creates scheduler-related tables

### 🧹 maintenance/
System maintenance and cleanup tools:
- (Future maintenance scripts go here)

## 💡 Usage

All utility scripts can be run from the project root directory:

```bash
# Analysis scripts
python utils/analysis/analyze_recommendation_behavior.py

# Database utilities  
python utils/database/check_recommendations.py

# Debugging tools
python utils/debugging/check_logs.py

# Setup scripts
python utils/setup/create_recommendations_table.py
```

## 📋 Notes

- All utilities are designed to be run independently
- Scripts maintain backward compatibility with existing functionality
- Each subdirectory focuses on a specific aspect of system management
- New utilities should be placed in the appropriate subdirectory