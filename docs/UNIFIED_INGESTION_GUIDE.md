# Unified Document Ingestion System

## Overview

A single, robust ingestion script that handles all document types and code repositories. **Gracefully handles missing files/folders without throwing errors.**

## Key Features

✅ **Smart Ingestion** - Skips already ingested files automatically  
✅ **Error Handling** - Missing folders don't cause failures  
✅ **Multi-Format** - PDF, DOCX, TXT, and code files  
✅ **Progress Tracking** - Real-time progress and statistics  
✅ **Configurable** - Easy configuration via `ingestion_config.py`  
✅ **Safe** - No re-ingestion of existing documents  

## Quick Start

### 1. Run with defaults:
```bash
python ingest_unified.py
```

### 2. Customize configuration:
Edit `ingestion_config.py`:
```python
# Add new document categories
DOCUMENT_CATEGORIES = {
    "proposals/type-1": "proposals_sorting_conveyor",
    "manuals": "technical_manuals",
    "new_folder": "new_category"  # Add your own
}

# Add code repositories
CODE_REPOSITORIES = [
    {
        "path": r"C:\path\to\your\code",
        "category": "your-code",
        "enabled": True
    }
]
```

### 3. Run again:
```bash
python ingest_unified.py
```

## What It Does

### Documents
- Searches configured folders for PDFs, DOCX, TXT files
- Skips folders that don't exist (no errors)
- Checks if already ingested (by filename)
- Processes new documents only
- Extracts text and creates embeddings
- Adds to vector store with category metadata

### Code
- Scans code repositories for supported languages
- Python (.py), C# (.cs), JavaScript (.js), TypeScript (.ts), etc.
- Skips already ingested files
- Chunks code intelligently
- Preserves file structure and metadata

## Configuration

### Document Settings (`ingestion_config.py`)

```python
# Base path
DOCUMENTS_BASE_PATH = "app/modules/neo_chatbot/data/documents"

# Categories (folder: category_name)
DOCUMENT_CATEGORIES = {
    "proposals/type-1": "proposals_sorting_conveyor",
    "support": "technical_support",
    ".": "general_documentation"  # root folder
}

# Advanced settings
CHUNK_SIZE = 1000          # Characters per chunk
CHUNK_OVERLAP = 200        # Overlap between chunks
ENABLE_OCR = True          # Extract text from images
SKIP_EXISTING = True       # Skip already ingested files
```

### Code Settings

```python
# Enable/disable
ENABLE_CODE_INGESTION = True

# Repositories
CODE_REPOSITORIES = [
    {
        "path": r"C:\full\path\to\codebase",
        "category": "project-code",
        "description": "Optional description",
        "enabled": True  # Set False to skip
    }
]
```

## Graceful Error Handling

The system handles these scenarios without crashing:

### Missing Folders
```
⚠️ Folder not found: proposals/type-4
   Skipping...
✅ Continuing with next folder
```

### Missing Base Path
```
⚠️ Base path not found: documents
   Creating directory...
✅ Created: documents
```

### Missing Code Repository
```
⚠️ Path not found: C:\missing\repo
   Skipping...
✅ Continuing with next repository
```

### Unsupported File Types
```
⚠️ Unsupported format: .xlsx
   Skipping...
```

### Processing Errors
```
❌ Failed: filename.pdf
   Error: Could not extract text
📊 Logged to failed_items
✅ Continuing with remaining files
```

## Output Example

```
================================================================================
🚀 UNIFIED INGESTION SYSTEM
   Smart ingestion of all documents and code
================================================================================

📊 Found 45 files already ingested

================================================================================
📄 DOCUMENT INGESTION
================================================================================

────────────────────────────────────────────────────────────────────────────
📁 Category: proposals_sorting_conveyor
   Path: app/modules/neo_chatbot/data/documents/proposals/type-1
   Found: 12 documents

   [1/12] NEO_Proposal_Sorter_v2.pdf
      ✅ Success: 45 chunks (45,234 chars)
   
   [2/12] Conveyor_System_Specs.pdf
      ⏭️ Already ingested
   
   ...

────────────────────────────────────────────────────────────────────────────
📁 Category: proposals_warehouse_automation
   Path: app/modules/neo_chatbot/data/documents/proposals/type-2
   ⚠️ Folder not found - skipping

================================================================================
💻 CODE INGESTION
================================================================================

────────────────────────────────────────────────────────────────────────────
📂 Repository: neo-fleet-manager-noon-min-2.0
   Path: C:\Users\...\neo-fleet-manager-noon-min-2.0
   Category: neo-fleet-manager-code
   
   Total files: 234
   New files: 12
   Already ingested: 222
   
   Processing 12 new files...
      [1/12] WarehouseController.cs
      [2/12] BinManager.cs
      ...
   
   ✅ Repository complete:
      New: 12
      Failed: 0

================================================================================
📊 INGESTION SUMMARY
================================================================================

📄 DOCUMENTS:
   Found: 25
   ✅ Newly ingested: 8
   ⏭️ Skipped: 15
   ❌ Failed: 2

💻 CODE FILES:
   Found: 234
   ✅ Newly ingested: 12
   ⏭️ Skipped: 222
   ❌ Failed: 0

📊 OVERALL:
   Total items: 259
   ✅ Newly ingested: 20
   ⏭️ Skipped: 237
   ❌ Failed: 2

================================================================================
📊 VECTOR STORE STATISTICS
================================================================================

Total chunks: 2,345
Unique files: 65

By category:
   proposals_sorting_conveyor: 456
   proposals_warehouse_automation: 234
   neo-fleet-manager-code: 1,234
   technical_support: 123

================================================================================

✅ Ingestion complete!

💡 You can now query the chatbot about:
   📄 Documents: Technical proposals, support docs, manuals
   💻 Code: Implementation details, functions, classes

================================================================================
```

## Comparison with Old Scripts

| Feature | Old Scripts | Unified Script |
|---------|------------|----------------|
| **Multiple files** | Yes (5+ scripts) | No (single script) |
| **Missing folders** | ❌ Throws errors | ✅ Gracefully skips |
| **Duplicate checking** | Manual | ✅ Automatic |
| **Configuration** | Hardcoded | ✅ Config file |
| **Progress tracking** | Basic | ✅ Detailed |
| **Error recovery** | ❌ Stops on error | ✅ Continues |
| **Summary report** | Limited | ✅ Comprehensive |

## Adding New Document Types

Currently supported: PDF

To add support for DOCX, TXT, etc., extend the ingestion logic:

```python
# In ingest_unified.py, UnifiedIngestionSystem.ingest_documents()

if file_path.suffix.lower() == '.pdf':
    result = self.doc_processor.ingest_pdf(str(file_path), category)
elif file_path.suffix.lower() == '.docx':
    result = self.doc_processor.ingest_docx(str(file_path), category)
elif file_path.suffix.lower() == '.txt':
    result = self.doc_processor.ingest_txt(str(file_path), category)
```

## Troubleshooting

### No documents found
- Check `DOCUMENTS_BASE_PATH` in `ingestion_config.py`
- Verify folder structure exists
- Check file extensions (case-sensitive: .pdf vs .PDF)

### Code ingestion not working
- Set `ENABLE_CODE_INGESTION = True` in config
- Check repository path exists
- Verify `enabled: True` for each repository

### All files skipped
- Files already ingested
- Clear vector store to re-ingest: Delete `chroma_db` folder
- Or set `SKIP_EXISTING = False` (not recommended)

### Permission errors
- Run as administrator (Windows)
- Check file/folder permissions
- Ensure files aren't locked/in use

## Old Scripts (Now Deprecated)

You can safely use only `ingest_unified.py` instead of:
- ~~`ingest_proposals.py`~~
- ~~`ingest_all_proposals.py`~~
- ~~`ingest_all_documents.py`~~
- ~~`ingest_neo_code.py`~~
- ~~`ingest_code_interactive.py`~~

Keep them for reference, but use `ingest_unified.py` going forward.

## Benefits

✅ **Single entry point** - One script for everything  
✅ **Error resilient** - Missing folders don't break the flow  
✅ **Smart** - Skips already ingested files  
✅ **Configurable** - Easy to customize via config file  
✅ **Comprehensive** - Detailed progress and summary  
✅ **Safe** - Won't duplicate or overwrite existing data  

## Next Steps

1. **Run the script**: `python ingest_unified.py`
2. **Check the summary** - Review what was ingested
3. **Test the chatbot** - Ask questions about ingested content
4. **Add more content** - Edit config and re-run (only new items will be added)
