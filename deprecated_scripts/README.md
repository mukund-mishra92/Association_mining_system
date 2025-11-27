# Deprecated Ingestion Scripts

These scripts have been **replaced by the unified ingestion system**.

## ⚠️ DO NOT USE THESE FILES

Use `ingest_unified.py` instead - it does everything these scripts did, but better.

## What's Here

### Old Document Ingestion Scripts
- `ingest_proposals.py` - OLD: Only ingested proposal documents
- `ingest_all_proposals.py` - OLD: Batch ingestion of all proposals
- `ingest_all_documents.py` - OLD: Documents + code ingestion
- `reingest_with_huggingface.py` - OLD: Re-ingestion with specific embeddings

### Old Code Ingestion Scripts  
- `ingest_neo_code.py` - OLD: Only ingested NEO codebase
- `ingest_code_interactive.py` - OLD: Interactive code ingestion
- `ingest_code_quick_start.bat` - OLD: Batch file for code ingestion

## Why Deprecated?

### Problems with Old Scripts
- ❌ Multiple scripts for different purposes (confusing)
- ❌ Hardcoded paths (not configurable)
- ❌ No error handling (crashed on missing folders)
- ❌ No duplicate detection (could re-ingest same files)
- ❌ Difficult to maintain (5+ separate scripts)

### New Unified System
- ✅ Single script: `ingest_unified.py`
- ✅ Configuration file: `ingestion_config.py`
- ✅ Graceful error handling (missing folders don't crash)
- ✅ Smart duplicate detection (skips already ingested)
- ✅ Easy to maintain (one source of truth)

## Migration

Instead of these old scripts, use:

```bash
# NEW WAY - One command for everything
python ingest_unified.py
```

Configure what to ingest in `ingestion_config.py`:

```python
# Documents
DOCUMENT_CATEGORIES = {
    "proposals/type-1": "proposals_sorting_conveyor",
    # Add more...
}

# Code repositories
CODE_REPOSITORIES = [
    {
        "path": r"C:\your\codebase",
        "category": "your-code",
        "enabled": True
    }
]
```

## Why Keep These Files?

These files are kept for:
- **Reference** - In case you need to see old implementation
- **Comparison** - Understand what changed
- **Backup** - Safety net during transition

## Can I Delete These?

**Yes**, but only if:
- ✅ You've tested `ingest_unified.py` successfully
- ✅ You've migrated all your custom configurations
- ✅ You have version control/backups

**No**, if:
- ❌ Still testing the new system
- ❌ Have custom code in these scripts
- ❌ Want reference for how things worked before

## Documentation

For the new unified system, see:
- `UNIFIED_INGESTION_GUIDE.md` - Complete guide
- `INGESTION_QUICK_REFERENCE.md` - Quick reference
- `INGESTION_CONSOLIDATION_SUMMARY.md` - What changed and why

---

**Last Updated:** November 27, 2025  
**Status:** Deprecated - Use `ingest_unified.py` instead
