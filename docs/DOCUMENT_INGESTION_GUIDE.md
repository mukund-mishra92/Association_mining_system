# Document Ingestion Issues & Solutions

## Your Questions Answered

### 1. What's the "Unknown error" about?

The error message `❌ Failed: Unknown error` appears when the ingestion script catches an exception but doesn't have a specific error message. This typically happens when:

**Common Causes:**
- PDF file is corrupted or unreadable
- PDF has no extractable text (all images, no OCR available)
- Embedding generation fails (LLM API error)
- Memory issues with large PDF files
- File access permissions

**How to see the actual error:**
The full error details are in the logs. Look for the line just before "Unknown error" - it should have more details.

### 2. Will previous documents be kept?

**YES! ✅ Documents are PRESERVED during ingestion!**

Here's how it works:

#### Document Storage Location
```
app/modules/neo_chatbot/data/vector_store.json
```

#### How It Works:
```python
# When adding documents (line 94-109 in vector_store_service.py):

def add_documents_batch(self, documents: List[Dict[str, Any]]):
    for doc in documents:
        # Check if document already exists by ID
        existing_index = next((i for i, d in enumerate(self.documents) if d["id"] == doc["id"]), None)
        
        if existing_index is not None:
            self.documents[existing_index] = doc  # ✅ UPDATE existing
        else:
            self.documents.append(doc)           # ✅ ADD new
    
    self.save_store()  # Save all documents (old + new)
```

**Key Points:**
1. ✅ **Existing documents are KEPT** - They stay in the vector store
2. ✅ **New documents are ADDED** - Appended to the existing list
3. ✅ **Updates by ID** - If same document ID exists, it updates instead of duplicating
4. ✅ **All saved together** - Single JSON file contains all documents

#### Document ID Format:
```python
doc_id = f"{file_path.stem}_chunk_{i}_{uuid.uuid4().hex[:8]}"

Example: "proposal_ABC_chunk_0_a1b2c3d4"
```

Each time you ingest the SAME file, it gets a NEW random ID, so:
- ⚠️ **Re-ingesting same file creates duplicates** (different UUIDs)
- ✅ **New files are added without removing old ones**

---

## Solution: Ingest All Documents Properly

### Option 1: Check Current Vector Store

First, see what's already there:

```python
python check_vector_store.py
```

This will show:
- Total documents
- Documents by category
- Documents by filename

### Option 2: Ingest Only New Documents

If you have new documents only in `proposals` folder:

```python
python ingest_all_proposals.py
```

This will:
- ✅ Keep all existing documents
- ✅ Add new proposal documents
- ⚠️ May create duplicates if you run it twice

### Option 3: Ingest ALL Documents from Scratch

If you want to ensure ALL documents in the `documents` folder are ingested:

**Step 1: Check what's currently ingested**
```python
python check_vector_store.py
```

**Step 2: Back up existing vector store (optional)**
```powershell
Copy-Item app\modules\neo_chatbot\data\vector_store.json app\modules\neo_chatbot\data\vector_store_backup.json
```

**Step 3: Run full ingestion**

I'll create a script for you:

```python
# ingest_all_documents.py
"""
Ingest ALL documents from the documents folder
Checks existing vector store and only adds missing documents
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from app.modules.neo_chatbot.scripts.ingest_documents import DocumentProcessor
from app.modules.neo_chatbot.services.vector_store_service import VectorStoreService

def main():
    print("\n" + "="*80)
    print("📚 FULL DOCUMENT INGESTION")
    print("="*80)
    
    # Initialize services
    processor = DocumentProcessor()
    vs = VectorStoreService()
    
    # Get existing documents
    existing_files = set()
    for doc in vs.documents:
        filename = doc.get('metadata', {}).get('filename', '')
        if filename:
            existing_files.add(filename)
    
    print(f"\n📊 Current Status:")
    print(f"   Total documents in vector store: {len(vs.documents)}")
    print(f"   Unique files: {len(existing_files)}")
    
    # Base documents folder
    docs_base = Path("app/modules/neo_chatbot/data/documents")
    
    # Categories to process
    categories = {
        "proposals/type-1": "proposals_sorting_conveyor",
        "proposals/type-2": "proposals_warehouse_automation",
        "proposals/type-3": "proposals_specialized_systems",
        "support": "technical_support",
        ".": "general_documentation"  # Root documents folder
    }
    
    total_found = 0
    total_new = 0
    total_skipped = 0
    total_failed = 0
    
    for folder, category in categories.items():
        folder_path = docs_base / folder
        
        if not folder_path.exists():
            print(f"\n⚠️  Folder not found: {folder_path}")
            continue
        
        print(f"\n{'='*80}")
        print(f"📁 Processing: {folder}")
        print(f"   Category: {category}")
        print(f"{'='*80}\n")
        
        # Find all PDFs
        pdf_files = list(folder_path.glob("*.pdf"))
        total_found += len(pdf_files)
        
        print(f"Found {len(pdf_files)} PDF files\n")
        
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"[{i}/{len(pdf_files)}] {pdf_file.name}")
            
            # Check if already ingested
            if pdf_file.name in existing_files:
                print(f"   ⏭️  Already ingested - skipping")
                total_skipped += 1
                continue
            
            # Ingest new document
            try:
                result = processor.ingest_pdf(str(pdf_file), category)
                
                if result.get("status") == "success":
                    total_new += 1
                    print(f"   ✅ Success: {result.get('chunks', 0)} chunks")
                else:
                    total_failed += 1
                    error_msg = result.get('message', 'Unknown error')
                    print(f"   ❌ Failed: {error_msg}")
                    
            except Exception as e:
                total_failed += 1
                print(f"   ❌ Error: {str(e)[:100]}")
    
    # Final summary
    print("\n" + "="*80)
    print("📊 FINAL SUMMARY")
    print("="*80)
    print(f"\n📄 Total PDF files found: {total_found}")
    print(f"✅ Newly ingested: {total_new}")
    print(f"⏭️  Skipped (already exists): {total_skipped}")
    print(f"❌ Failed: {total_failed}")
    
    # Updated vector store stats
    vs_updated = VectorStoreService()
    print(f"\n📊 Updated Vector Store:")
    print(f"   Total documents: {len(vs_updated.documents)}")
    
    stats = vs_updated.get_stats()
    print(f"\n   Documents by category:")
    for cat, count in stats.get('by_category', {}).items():
        print(f"      {cat}: {count}")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
```

**Save this as**: `ingest_all_documents.py` in the root folder.

---

## Troubleshooting the "Unknown error"

### Step 1: Run with detailed logging

Modify `ingest_all_proposals.py` to catch the actual error:

```python
# Around line 62, replace:
try:
    result = processor.ingest_pdf(str(pdf_file), category)
    
    if result.get("success"):
        total_success += 1
        total_chunks += result.get("chunks", 0)
        print(f"   ✅ Success: {result.get('chunks', 0)} chunks")
    else:
        total_failed += 1
        print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
        
except Exception as e:
    total_failed += 1
    print(f"   ❌ Error: {str(e)[:100]}")
```

Change to:

```python
try:
    result = processor.ingest_pdf(str(pdf_file), category)
    
    if result.get("status") == "success":  # ⬅️ Changed from "success" to check "status"
        total_success += 1
        total_chunks += result.get("chunks", 0)
        print(f"   ✅ Success: {result.get('chunks', 0)} chunks")
    else:
        total_failed += 1
        error_msg = result.get('message', result.get('error', 'Unknown error'))
        print(f"   ❌ Failed: {error_msg}")
        print(f"      File: {pdf_file}")  # ⬅️ Show which file failed
        
except Exception as e:
    total_failed += 1
    print(f"   ❌ Error: {str(e)}")  # ⬅️ Show full error
    print(f"      File: {pdf_file}")
    import traceback
    print(traceback.format_exc())  # ⬅️ Show full stack trace
```

### Step 2: Check the specific file

The error occurred while processing:
```
FK_Kalash_Technocommercial Offer_Option 2_18-11-2023 (1).pdf
```

Try to manually check this file:

```python
# test_single_file.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from app.modules.neo_chatbot.scripts.ingest_documents import DocumentProcessor

processor = DocumentProcessor()
file_path = "app/modules/neo_chatbot/data/documents/proposals/type-3/FK_Kalash_Technocommercial Offer_Option 2_18-11-2023 (1).pdf"

print(f"Testing file: {file_path}")
result = processor.ingest_pdf(file_path, "test_category")

print(f"\nResult: {result}")
```

### Step 3: Common issues and fixes

**Issue 1: PDF has no text (scanned images)**
```
Solution: Enable OCR in DocumentProcessor
Currently OCR is disabled by default
```

**Issue 2: LLM API errors (embedding generation)**
```
Solution: Check your OpenAI/Azure API key in .env
The system falls back to hash-based embeddings if LLM fails
```

**Issue 3: Memory issues**
```
Solution: Process files in smaller batches
Or increase chunk size to reduce number of chunks
```

---

## Best Practices

### 1. Check Before Ingesting
```python
python check_vector_store.py
```

### 2. Backup Before Major Changes
```powershell
Copy-Item app\modules\neo_chatbot\data\vector_store.json app\modules\neo_chatbot\data\vector_store_backup.json
```

### 3. Ingest Incrementally
- Don't re-ingest already processed files
- Keep track of what's been ingested
- Use categories to organize

### 4. Monitor the Logs
- Look for actual error messages
- Check which files fail
- Verify chunk counts make sense

### 5. Test Individual Files First
- If a file fails, test it separately
- Check if it's readable
- Verify it has extractable text

---

## Quick Commands

```powershell
# Check current vector store
python check_vector_store.py

# Ingest only proposals
python ingest_all_proposals.py

# Ingest all documents (new script above)
python ingest_all_documents.py

# Backup vector store
Copy-Item app\modules\neo_chatbot\data\vector_store.json app\modules\neo_chatbot\data\vector_store_backup.json

# Restore from backup
Copy-Item app\modules\neo_chatbot\data\vector_store_backup.json app\modules\neo_chatbot\data\vector_store.json
```

---

## Summary

✅ **Your previous documents are SAFE** - they won't be deleted  
✅ **New ingestion ADDS to existing** - doesn't replace  
⚠️ **Re-ingesting creates duplicates** - same file gets new IDs  
❌ **"Unknown error"** - need to see full error message for diagnosis

**Recommendation:**
1. Check what's currently in vector store
2. Only ingest NEW documents you haven't processed yet
3. Fix the specific failing file by examining the full error
4. Consider backing up before major ingestion runs
