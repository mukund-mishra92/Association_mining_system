# Quick Reference: Unified Ingestion System

## 🚀 Quick Start

### Run Everything (Default)
```bash
python ingest_unified.py
```

### What It Does
✅ Scans configured folders for documents  
✅ Checks configured code repositories  
✅ Skips already ingested files automatically  
✅ Handles missing folders gracefully (no errors!)  
✅ Shows comprehensive progress and statistics  

---

## ⚙️ Configuration

### Edit Settings
```bash
# Open this file:
ingestion_config.py
```

### Add Document Category
```python
DOCUMENT_CATEGORIES = {
    "my_new_folder": "my_category",  # Add this line
    # ...existing categories...
}
```

### Add Code Repository
```python
CODE_REPOSITORIES = [
    {
        "path": r"C:\path\to\your\code",
        "category": "your-code",
        "enabled": True  # Set False to skip
    },
    # ...existing repositories...
]
```

### Disable Code Ingestion
```python
ENABLE_CODE_INGESTION = False
```

---

## 📁 File Structure

```
association_mining_system/
├── ingest_unified.py              ← Main script (RUN THIS)
├── ingestion_config.py           ← Edit configuration here
├── UNIFIED_INGESTION_GUIDE.md   ← Full documentation
└── app/modules/neo_chatbot/data/
    └── documents/                ← Put documents here
        ├── proposals/
        │   ├── type-1/          ← PDF files
        │   ├── type-2/          ← PDF files
        │   └── type-3/          ← PDF files
        ├── support/             ← Support docs
        ├── manuals/             ← Manuals
        └── ...                  ← Add more folders
```

---

## 🎯 Common Tasks

### Ingest New Documents
```bash
1. Put PDFs in configured folder (e.g., documents/proposals/type-1/)
2. Run: python ingest_unified.py
3. Check summary - only new files are ingested
```

### Re-ingest Everything
```bash
1. Delete chroma_db folder (vector store)
2. Run: python ingest_unified.py
```

### Check What's Ingested
```bash
python check_vector_store.py
```

### Add New Document Type
```bash
1. Create folder: documents/new_type/
2. Edit ingestion_config.py:
   DOCUMENT_CATEGORIES = {
       "new_type": "new_category"
   }
3. Run: python ingest_unified.py
```

---

## ✅ What Gets Handled

### Documents
- ✅ PDF files (`.pdf`, `.PDF`)
- ⏭️ Already ingested files (skipped automatically)
- ⚠️ Missing folders (warning, continues)
- ⚠️ Corrupted files (logged, continues)

### Code
- ✅ Python (`.py`)
- ✅ C# (`.cs`)
- ✅ JavaScript/TypeScript (`.js`, `.ts`)
- ✅ Java (`.java`)
- ⏭️ Already ingested files (skipped)
- ⏭️ Binary/generated files (skipped)

---

## 📊 Output Example

```
🚀 UNIFIED INGESTION SYSTEM
══════════════════════════════════════

📊 Found 45 files already ingested

📄 DOCUMENT INGESTION
──────────────────────────────────────
📁 Category: proposals_sorting_conveyor
   Found: 12 documents
   
   [1/12] NEO_Proposal_v2.pdf
      ✅ Success: 45 chunks
   [2/12] Specs.pdf
      ⏭️ Already ingested

💻 CODE INGESTION
──────────────────────────────────────
📂 Repository: neo-fleet-manager
   Total files: 234
   New files: 12
   Already ingested: 222
   
   ✅ Repository complete

📊 INGESTION SUMMARY
══════════════════════════════════════
📄 DOCUMENTS: 8 new, 15 skipped, 2 failed
💻 CODE: 12 new, 222 skipped, 0 failed

✅ Ingestion complete!
```

---

## 🔧 Troubleshooting

### No documents found
```bash
# Check paths in ingestion_config.py
DOCUMENTS_BASE_PATH = "app/modules/neo_chatbot/data/documents"

# Verify folder exists:
dir app\modules\neo_chatbot\data\documents
```

### Code not ingesting
```bash
# Check if enabled:
ENABLE_CODE_INGESTION = True

# Check repository path exists:
dir C:\path\to\codebase
```

### All files skipped
```bash
# Normal - means files already ingested!
# To re-ingest: Delete chroma_db folder
```

### Permission error
```bash
# Run as administrator (Windows)
# Or check file permissions
```

---

## 🎓 Key Concepts

### Smart Duplicate Detection
- Checks filenames before ingesting
- Skips if already in vector store
- Fast and efficient

### Graceful Error Handling
- Missing folder? ⚠️ Warning + continue
- Corrupted file? ⚠️ Log + continue  
- Invalid path? ⚠️ Skip + continue
- **Never crashes the entire process!**

### Category-Based Organization
- Documents grouped by category
- Easy filtering during retrieval
- Better search accuracy

---

## 📖 Full Documentation

For complete details, see:
- **UNIFIED_INGESTION_GUIDE.md** - Complete user guide
- **INGESTION_CONSOLIDATION_SUMMARY.md** - What changed and why

---

## 🆘 Quick Help

| Issue | Solution |
|-------|----------|
| Script not found | `cd` to project root first |
| Missing folders | It's OK! Script handles it |
| All files skipped | Normal - already ingested |
| Want to re-ingest | Delete `chroma_db` folder |
| Change categories | Edit `ingestion_config.py` |
| Add new folders | Edit config + create folder |

---

**That's it! Just run `python ingest_unified.py` and it handles everything! 🎉**
