# Embedding Size Mismatch - Complete Guide

## ⚠️ YES, Embedding Size Mismatch IS Possible!

### The Problem

Your system uses **TWO DIFFERENT embedding dimensions**:

#### 1. **During Ingestion** (ingest_documents.py)
```python
# Line 169-192 in ingest_documents.py
def get_embedding(self, text: str) -> List[float]:
    try:
        embedding = self.llm_service.generate_embedding(text)
        return embedding
    except Exception as e:
        # FALLBACK: Uses 384 dimensions
        return embedding[:384]  # ⚠️ 384 dimensions
```

**Fallback creates**: **384-dimensional** vectors

#### 2. **During Query** (llm_service.py)
```python
# Line 301-335 in llm_service.py
def generate_embedding(self, text: str) -> List[float]:
    if self.provider == "openai" and self.openai_client:
        response = self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding  # OpenAI: 1536 dimensions
    else:
        # FALLBACK: Returns 1536 dimensions
        return [0.0] * 1536  # ⚠️ 1536 dimensions
```

**OpenAI creates**: **1536-dimensional** vectors  
**Fallback creates**: **1536-dimensional** vectors

---

## 🔴 The Mismatch Scenarios

### Scenario 1: Ingestion with OpenAI, Query with Fallback
```
Ingestion: OpenAI API working → 1536 dimensions stored
Query:     OpenAI API fails    → 1536 dimensions (mock)
Result:    ✅ WORKS (same size)
```

### Scenario 2: Ingestion with Fallback, Query with OpenAI
```
Ingestion: OpenAI API fails    → 384 dimensions stored
Query:     OpenAI API working  → 1536 dimensions
Result:    ❌ MISMATCH ERROR!
```

### Scenario 3: Ingestion with Fallback, Query with Fallback (LLM)
```
Ingestion: OpenAI API fails    → 384 dimensions stored
Query:     OpenAI API fails    → 1536 dimensions (mock)
Result:    ❌ MISMATCH ERROR!
```

---

## 🔍 Where to Check

### 1. Check Your Existing Vector Store

```python
# check_embedding_dimensions.py
import json
from pathlib import Path

vector_store_path = Path("app/modules/neo_chatbot/data/vector_store.json")

if vector_store_path.exists():
    with open(vector_store_path, 'r') as f:
        data = json.load(f)
    
    if data:
        first_doc = data[0]
        embedding_size = len(first_doc.get('embedding', []))
        print(f"Current embedding dimension: {embedding_size}")
        
        # Check all documents
        sizes = set()
        for doc in data:
            sizes.add(len(doc.get('embedding', [])))
        
        if len(sizes) > 1:
            print(f"⚠️ INCONSISTENT DIMENSIONS FOUND: {sizes}")
        else:
            print(f"✅ All documents have consistent dimension: {list(sizes)[0]}")
    else:
        print("Vector store is empty")
else:
    print("No vector store found")
```

**Run this:**
```powershell
python check_embedding_dimensions.py
```

### 2. Check Your .env Configuration

```bash
# Check if OpenAI API key is set
OPENAI_API_KEY=sk-...your-key...
GROQ_API_KEY=...your-groq-key...
```

**If OpenAI key is missing or invalid:**
- Ingestion will use **384-dim fallback**
- Query will use **1536-dim mock**
- Result: **MISMATCH ERROR** ❌

---

## 🔧 Solutions

### Solution 1: Force Consistent Embedding Size (RECOMMENDED)

Fix the **ingest_documents.py** fallback to match **llm_service.py**:

**File**: `app/modules/neo_chatbot/scripts/ingest_documents.py`  
**Line**: ~179-192

**Change from:**
```python
# Fallback to hash-based approach (384 dimensions)
import hashlib
text_hash = hashlib.sha256(text.encode()).hexdigest()
embedding = []

for i in range(0, len(text_hash), 2):
    byte_val = int(text_hash[i:i+2], 16)
    embedding.append(float(byte_val) / 255.0)

# Pad to 384 dimensions
while len(embedding) < 384:
    embedding.append(0.0)

return embedding[:384]  # ❌ 384 dimensions
```

**Change to:**
```python
# Fallback to hash-based approach (1536 dimensions to match OpenAI)
import hashlib
text_hash = hashlib.sha256(text.encode()).hexdigest()
embedding = []

for i in range(0, len(text_hash), 2):
    byte_val = int(text_hash[i:i+2], 16)
    embedding.append(float(byte_val) / 255.0)

# Pad to 1536 dimensions (same as OpenAI text-embedding-3-small)
while len(embedding) < 1536:
    # Repeat the hash pattern
    hash_index = len(embedding) % len(text_hash)
    byte_val = int(text_hash[hash_index:hash_index+2], 16) if hash_index + 2 <= len(text_hash) else 0
    embedding.append(float(byte_val) / 255.0)

return embedding[:1536]  # ✅ 1536 dimensions
```

### Solution 2: Use OpenAI API for Everything

**Ensure OpenAI API key is configured:**

```bash
# In .env file
OPENAI_API_KEY=sk-your-actual-openai-key
```

**Benefits:**
- ✅ Consistent 1536 dimensions
- ✅ High-quality embeddings
- ✅ Better search accuracy

**Drawbacks:**
- 💰 Costs money (but very cheap for embeddings)
- 🌐 Requires internet connection

### Solution 3: Re-ingest All Documents

If you already have documents with 384-dim embeddings:

**Option A: Delete and Re-ingest**
```powershell
# Backup first
Copy-Item app\modules\neo_chatbot\data\vector_store.json app\modules\neo_chatbot\data\vector_store_backup.json

# Delete old vector store
Remove-Item app\modules\neo_chatbot\data\vector_store.json

# Re-ingest all documents
python ingest_all_documents.py
```

**Option B: Convert Existing Embeddings**
```python
# convert_embeddings.py
import json
from pathlib import Path
import hashlib

def convert_embedding(old_embedding, text):
    """Convert 384-dim to 1536-dim"""
    # Pad with hash-based values
    text_hash = hashlib.sha256(text.encode()).hexdigest()
    new_embedding = old_embedding.copy()
    
    while len(new_embedding) < 1536:
        hash_index = len(new_embedding) % len(text_hash)
        byte_val = int(text_hash[hash_index:hash_index+2], 16) if hash_index + 2 <= len(text_hash) else 0
        new_embedding.append(float(byte_val) / 255.0)
    
    return new_embedding[:1536]

vector_store_path = Path("app/modules/neo_chatbot/data/vector_store.json")

# Load
with open(vector_store_path, 'r') as f:
    data = json.load(f)

# Convert
converted = 0
for doc in data:
    if len(doc['embedding']) == 384:
        doc['embedding'] = convert_embedding(doc['embedding'], doc['content'])
        converted += 1

# Save
with open(vector_store_path, 'w') as f:
    json.dump(data, f, indent=2)

print(f"✅ Converted {converted} documents from 384 to 1536 dimensions")
```

---

## 📋 Step-by-Step Fix (RECOMMENDED)

### Step 1: Check Current State
```powershell
python check_embedding_dimensions.py
```

### Step 2: Fix the Code

**Edit**: `app\modules\neo_chatbot\scripts\ingest_documents.py`

**Find** (around line 179):
```python
# Pad to 384 dimensions
while len(embedding) < 384:
    embedding.append(0.0)

return embedding[:384]
```

**Replace with**:
```python
# Pad to 1536 dimensions (same as OpenAI text-embedding-3-small)
while len(embedding) < 1536:
    # Repeat the hash pattern for more dimensions
    hash_index = len(embedding) % len(text_hash)
    if hash_index + 2 <= len(text_hash):
        byte_val = int(text_hash[hash_index:hash_index+2], 16)
        embedding.append(float(byte_val) / 255.0)
    else:
        embedding.append(0.0)

return embedding[:1536]
```

### Step 3: Handle Existing Documents

**If you have existing documents with 384 dimensions:**

**Option A: Delete and re-ingest**
```powershell
# Backup
Copy-Item app\modules\neo_chatbot\data\vector_store.json app\modules\neo_chatbot\data\vector_store_backup_384.json

# Delete
Remove-Item app\modules\neo_chatbot\data\vector_store.json

# Re-ingest
python ingest_all_documents.py
```

**Option B: Convert existing (if you have many docs)**
```powershell
# Run the convert_embeddings.py script above
python convert_embeddings.py
```

### Step 4: Test Query

```python
# After re-ingestion, test a query
from app.modules.neo_chatbot.services.knowledge_base_service import KnowledgeBaseService

kb = KnowledgeBaseService()

# Try a search
response = kb.process_query(ChatRequest(
    message="What proposals do we have?",
    chatbot_type=ChatbotType.KNOWLEDGE_BASE,
    session_id="test"
))

print(response.response)
```

---

## 🎯 Quick Reference

### Where Embeddings are Generated

| Location | Purpose | Dimension | Fix Required? |
|----------|---------|-----------|---------------|
| `ingest_documents.py:173` | Document ingestion | 1536 (OpenAI) or **384** (fallback) | **YES** ✅ |
| `llm_service.py:314` | OpenAI embeddings | 1536 | NO ✅ |
| `llm_service.py:328` | Mock embeddings | 1536 | NO ✅ |
| `knowledge_base_service.py:91` | Query embedding | Uses llm_service (1536) | NO ✅ |

### File Locations to Check

```
📁 app/modules/neo_chatbot/
├── scripts/
│   └── ingest_documents.py        ← FIX THIS (line 179-192)
├── services/
│   ├── llm_service.py             ← Already correct (1536)
│   ├── knowledge_base_service.py  ← Already correct (uses llm_service)
│   └── vector_store_service.py    ← No changes needed
└── data/
    └── vector_store.json          ← Check dimension here
```

---

## 🔍 How to Detect the Error

**Error message you might see:**
```
ValueError: operands could not be broadcast together with shapes (384,) (1536,)
```

or

```
shapes (1536,) and (384,) not aligned
```

**In the logs:**
```
❌ Error searching vector store: shapes mismatch
⚠️ No results found from knowledge base
```

---

## 💡 Prevention

### Best Practices

1. **Always use OpenAI API if possible** (most reliable)
2. **Keep fallback dimension same as OpenAI** (1536)
3. **Test both ingestion and query** before production
4. **Check vector store dimensions** after ingestion
5. **Monitor logs** for embedding generation failures

### Environment Variables to Set

```bash
# .env file
OPENAI_API_KEY=sk-your-openai-key-here  # For real embeddings
GROQ_API_KEY=your-groq-key-here         # For LLM (doesn't do embeddings)
```

---

## 🧪 Testing Script

```python
# test_embeddings.py
"""Test embedding consistency"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from app.modules.neo_chatbot.services.llm_service import LLMService
from app.modules.neo_chatbot.scripts.ingest_documents import DocumentProcessor
from app.modules.neo_chatbot.services.vector_store_service import VectorStoreService

print("\n" + "="*80)
print("EMBEDDING DIMENSION TEST")
print("="*80)

# Test LLM service embeddings
print("\n1. Testing LLM Service embeddings (used during query):")
llm = LLMService()
test_text = "This is a test document"
query_embedding = llm.generate_embedding(test_text)
print(f"   Query embedding dimension: {len(query_embedding)}")

# Test DocumentProcessor embeddings
print("\n2. Testing DocumentProcessor embeddings (used during ingestion):")
processor = DocumentProcessor()
ingest_embedding = processor.get_embedding(test_text)
print(f"   Ingestion embedding dimension: {len(ingest_embedding)}")

# Check vector store
print("\n3. Checking existing vector store:")
vs = VectorStoreService()
if vs.documents:
    stored_dim = len(vs.documents[0]['embedding'])
    print(f"   Stored document embedding dimension: {stored_dim}")
    
    # Check for inconsistencies
    all_dims = set(len(doc['embedding']) for doc in vs.documents)
    if len(all_dims) > 1:
        print(f"   ⚠️ INCONSISTENT DIMENSIONS: {all_dims}")
    else:
        print(f"   ✅ All documents have consistent dimension: {list(all_dims)[0]}")
else:
    print("   Vector store is empty")

# Compare
print("\n4. Comparison:")
if len(query_embedding) == len(ingest_embedding):
    print(f"   ✅ MATCH: Query ({len(query_embedding)}) == Ingestion ({len(ingest_embedding)})")
else:
    print(f"   ❌ MISMATCH: Query ({len(query_embedding)}) != Ingestion ({len(ingest_embedding)})")
    print(f"   🔧 Action Required: Fix ingest_documents.py to use {len(query_embedding)} dimensions")

if vs.documents:
    if len(query_embedding) == stored_dim:
        print(f"   ✅ MATCH: Query ({len(query_embedding)}) == Stored ({stored_dim})")
    else:
        print(f"   ❌ MISMATCH: Query ({len(query_embedding)}) != Stored ({stored_dim})")
        print(f"   🔧 Action Required: Re-ingest documents or convert embeddings")

print("\n" + "="*80 + "\n")
```

**Run this:**
```powershell
python test_embeddings.py
```

---

## Summary

✅ **YES, embedding mismatch is possible**  
✅ **Where to check**: `ingest_documents.py` line 179-192  
✅ **What to change**: Change fallback from 384 to 1536 dimensions  
✅ **What to do with old data**: Re-ingest or convert  
✅ **How to test**: Run `test_embeddings.py`  

**The fix is simple: Make the fallback use 1536 dimensions instead of 384!**
