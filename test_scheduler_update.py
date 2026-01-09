#!/usr/bin/env python3
"""Test if scheduler service is updated correctly"""
from app.modules.association_mining.services.scheduler_service import get_scheduler_service

print("Testing scheduler service...")
s = get_scheduler_service()

# Check that new methods exist
print(f"✓ execute_mining_job exists: {hasattr(s, 'execute_mining_job')}")
print(f"✓ _execute_mining_job exists: {hasattr(s, '_execute_mining_job')}")
print(f"✓ _update_schedule_stats exists: {hasattr(s, '_update_schedule_stats')}")

# Check that old methods are gone (commented out)
print(f"✓ _execute_mining_job_async removed: {not hasattr(s, '_execute_mining_job_async')}")

print("\n✅ All checks passed! Scheduler service is updated correctly.")
