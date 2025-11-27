# NEO Chatbot - Accuracy Improvement Guide

## Problem Analysis

Based on your conversation examples, the chatbot exhibited several quality issues:

### 1. **Hallucinations** (Critical Issue)
- **Example**: Response about "different type of sorter service" invented 5 categories (Manual, Automated, Hybrid, Real-time, Batch) that don't exist in your documents
- **Impact**: Users receive false information not based on actual NEO system documentation
- **Root Cause**: LLM using general knowledge instead of strictly adhering to provided context

### 2. **Generic/Vague Responses**
- **Example**: "Various components work together" without listing specific components
- **Impact**: Responses lack technical depth and specificity users need
- **Root Cause**: Insufficient instruction to be specific and technical

### 3. **Poor Document Retrieval**
- **Example**: Relevance scores of 63-64% are too low
- **Impact**: Wrong documents retrieved, leading to incomplete or incorrect answers
- **Root Cause**: 
  - Too few documents retrieved (was 8, now 15)
  - Similarity threshold too low (was 0.25, now 0.30)
  - No query expansion for domain-specific terminology

### 4. **Missing Context**
- **Example**: User asks about "telescopic conveyor" but system doesn't find relevant docs
- **Impact**: Chatbot can't answer questions about documented features
- **Root Cause**: Query doesn't match document vocabulary

## Improvements Implemented

### 1. ✅ **Anti-Hallucination Prompting** (Response Agent)

**Changes Made**:
```python
**CRITICAL RULES - MUST FOLLOW**:
1. ONLY use information from the provided context
2. If context doesn't contain answer, explicitly state it
3. Be specific and technical - use exact terms from documents
4. Cite sources precisely
5. No generic statements without actual components from docs
6. Follow format instructions

**FORBIDDEN**:
❌ DO NOT invent categories, types, or classifications
❌ DO NOT use generic industry knowledge
❌ DO NOT assume features exist if not mentioned
❌ DO NOT provide theoretical advice
```

**Expected Impact**:
- **Before**: "Different types include: Manual, Automated, Hybrid..." (invented)
- **After**: "Based on documentation, the NEO system includes Cross-Belt Sorter (Document 3, page 15) with specifications: throughput 24,000 PPH, 58-369 destinations..."

### 2. ✅ **Hallucination Detection** (Verification Agent)

**Changes Made**:
```python
**PRIMARY MISSION**: Catch hallucinations and ensure 100% accuracy

**VERIFICATION CHECKLIST**:
1. Hallucination Detection - Flag statements not in context
2. Fact Verification - Every claim must have source
3. Citation Accuracy - Verify document references
4. Completeness Check - Add missed details from context
5. Format Preservation - Maintain required format

**CRITICAL RULES**:
- If Response Agent invented information, REMOVE it
- Replace vague statements with specific details
- DO NOT add your own knowledge
```

**Expected Impact**:
- Catches and removes hallucinated content
- Adds specific technical details from documents
- Ensures every statement is traceable to source

### 3. ✅ **Enhanced Document Retrieval**

**Changes Made**:
```python
# Increased from 8 to 15 documents
top_k=15

# Increased from 0.25 to 0.30 for better relevance
min_similarity=0.30

# Increased context per document from 500 to 800 chars
content = doc.get('content', '')[:800]

# Show 10 documents instead of 5 in context
for i, result in enumerate(search_results[:10], 1):
```

**Expected Impact**:
- More comprehensive context available to agents
- Better chance of finding specific technical details
- Higher quality documents (min similarity 0.30 vs 0.25)

### 4. ✅ **Query Expansion** (NEW Feature)

**Implementation**:
```python
def _expand_query_terms(self, query: str) -> str:
    """Expand query with domain-specific synonyms"""
    expansions = {
        "sorter": "sorter sortation cross-belt sorting chute destination",
        "conveyor": "conveyor conveyer belt roller powered accumulation telescopic",
        "sensor": "sensor scanner barcode 1D 2D RFID detection PLC",
        "induct": "induct induction GTC goods-to-conveyor put-away",
        "gtc": "GTC goods-to-conveyor station workstation pick",
        "robot": "robot bot NEO automated ASRS storage retrieval",
        # ... more mappings
    }
```

**Expected Impact**:
- **Before**: Query "what is telescopic conveyor" might miss docs with "telescopic extendable conveyor"
- **After**: Expanded to "telescopic conveyor extendable retractable loading unloading" catches more relevant docs

### 5. ✅ **Richer Context Format**

**Changes Made**:
```python
Document 1 - Relevance: 0.85
Source: F24-00543_UHP_Techno-commercial.pdf
Type: proposal
Page: 45
Content: [800 chars of actual content]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Expected Impact**:
- Agents see document type, page number, source file
- Easier to cite sources accurately
- More content per document for better understanding

## Additional Recommendations

### 1. **Document Chunking Strategy** (HIGH PRIORITY)

**Current Issue**: If documents aren't chunked well, relevant info might be split

**Recommendation**:
```bash
# Re-chunk documents with better overlap
python app/modules/neo_chatbot/scripts/rechunk_documents.py \
    --chunk-size 1000 \
    --chunk-overlap 200 \
    --preserve-context True
```

**Settings to Try**:
- Chunk size: 800-1200 tokens (current might be too small)
- Overlap: 150-250 tokens to maintain context across chunks
- Preserve section headers in chunks

### 2. **Add Metadata Filters** (MEDIUM PRIORITY)

**Recommendation**:
```python
# Filter by document type for better relevance
if "technical" in query or "specification" in query:
    filter_docs = ["proposal", "technical_spec"]
elif "how to" in query or "guide" in query:
    filter_docs = ["manual", "guide", "SOP"]

search_results = self.vector_store.search(
    query_embedding=query_embedding,
    top_k=15,
    min_similarity=0.30,
    filter={"document_type": {"$in": filter_docs}}  # Add filtering
)
```

### 3. **Improve Embeddings** (MEDIUM PRIORITY)

**Current**: HuggingFace default embeddings
**Recommendation**: Try domain-specific embeddings

```python
# Option 1: Fine-tune embeddings on your NEO documentation
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
# Fine-tune on your corpus

# Option 2: Use larger, more capable embedding model
model = SentenceTransformer('all-mpnet-base-v2')  # Better quality
```

### 4. **Add Terminology Glossary** (HIGH PRIORITY)

**Create**: `app/modules/neo_chatbot/data/glossary.json`
```json
{
  "GTC": "Goods-to-Conveyor station where operators pick totes for order consolidation",
  "Cross-Belt Sorter": "High-throughput sorting system with 24,000 PPH capacity, 58-369 destinations",
  "Telescopic Conveyor": "Extendable/retractable conveyor for loading/unloading, adjustable length",
  "ASRS": "Automated Storage and Retrieval System using NEO bots and storage grid",
  "Sorter PLC": "Programmable Logic Controller using Siemens S7 or Omron protocol",
  "ICR": "Image Character Recognition software for reading parcel labels"
}
```

**Usage**: Inject glossary terms into context when detected in query

### 5. **Query Classification** (LOW PRIORITY)

**Add intelligent routing**:
```python
def classify_query_type(self, query: str) -> str:
    """Classify query to adjust retrieval strategy"""
    if any(word in query.lower() for word in ["what is", "define", "meaning"]):
        return "definition"
    elif any(word in query.lower() for word in ["how to", "steps", "guide"]):
        return "procedural"
    elif any(word in query.lower() for word in ["types", "different", "categories"]):
        return "taxonomy"
    elif any(word in query.lower() for word in ["specification", "capacity", "throughput"]):
        return "technical"
    return "general"

# Adjust top_k and similarity based on type
if query_type == "technical":
    top_k = 20  # Need more docs for specs
    min_similarity = 0.35  # Higher threshold
elif query_type == "definition":
    top_k = 10  # Fewer docs needed
    min_similarity = 0.40  # Very high threshold
```

## Testing Strategy

### Test Cases to Validate Improvements

Create test file: `test_accuracy_improvements.py`

```python
test_cases = [
    {
        "query": "what are the different types of sorter services",
        "should_not_contain": ["Manual Sorter", "Automated Sorter", "Hybrid Sorter"],
        "should_contain": ["Cross-Belt Sorter", "Document"],
        "max_hallucination_score": 0.1
    },
    {
        "query": "what is telescopic conveyor",
        "should_contain": ["extendable", "retractable", "loading", "unloading"],
        "min_relevance": 0.75
    },
    {
        "query": "different sensors in sorter",
        "should_contain": ["barcode", "scanner", "PLC", "Document"],
        "should_not_contain": ["generally used", "typically includes"]
    },
    {
        "query": "what is GTC station",
        "should_contain": ["Goods-to-Conveyor", "operator", "pick", "tote"],
        "min_relevance": 0.80
    }
]
```

### Metrics to Track

1. **Hallucination Rate**: % of responses with invented information
   - Target: < 5% (currently ~30%)

2. **Average Document Relevance**: Mean similarity score
   - Target: > 0.75 (currently ~0.64)

3. **Answer Completeness**: % of queries fully answered
   - Target: > 85%

4. **Citation Accuracy**: % of claims with proper sources
   - Target: > 95%

5. **User Satisfaction**: Explicit feedback
   - Target: > 80% "helpful" ratings

## Expected Results

### Before Improvements
```
Query: "what are the different types of sorter services"
Response: "Different types include:
1. Manual Sorter Service - human operators sort parcels
2. Automated Sorter Service - machines sort parcels
3. Hybrid Sorter Service - combination of manual and automated
..."

Issues:
❌ Invented 5 categories not in documentation
❌ Generic industry knowledge, not NEO-specific
❌ No document citations
❌ Low relevance (63%)
```

### After Improvements
```
Query: "what are the different types of sorter services"
Response: "Based on the NEO system documentation, the primary sorter service is the **Cross-Belt Sorter System**:

**Cross-Belt Sorter** (📄 Document 3, Page 45):
- **Throughput**: Up to 24,000 parcels per hour (PPH)
- **Destinations**: 58-369 sorting destinations depending on configuration
- **Features**: 
  * Automatic 5-sided barcode scanning
  * Dimensioning and weighing capabilities
  * Image capture for verification
  * Integration with WCS via Siemens S7 or Omron PLC protocol

**Components** (📄 Document 4, Page 46):
- Sorter PLC: Controls sorting logic and directs parcels to chutes
- Barcode Scanners: 1D/2D scanning using TCP/IP protocol
- Image Services: Processes captured images during sortation

The documentation does not categorize multiple 'types' of sorter services. The NEO system uses this specific Cross-Belt configuration integrated with the WCS."

Improvements:
✅ ZERO invented information
✅ Specific technical details from docs
✅ Proper document citations with pages
✅ States when categorization doesn't exist in docs
✅ High relevance (85%+)
```

## Monitoring & Iteration

### 1. **Log Analysis**
Monitor `logs/` for:
- Queries with low relevance scores (< 0.70)
- Responses flagged by verification agent
- User feedback (helpful/not helpful)

### 2. **Weekly Review**
- Analyze top 20 "not helpful" responses
- Identify patterns in failed queries
- Add missing synonyms to query expansion
- Update glossary with new terms

### 3. **Document Coverage**
Run analytics:
```python
python app/modules/neo_chatbot/scripts/analyze_coverage.py
```
- Which documents are never retrieved?
- Which topics have low coverage?
- Where are the gaps?

## Implementation Checklist

- [x] ✅ Anti-hallucination prompting (Response Agent)
- [x] ✅ Hallucination detection (Verification Agent)
- [x] ✅ Increased document retrieval (15 docs, 0.30 threshold)
- [x] ✅ Query expansion with domain terms
- [x] ✅ Richer context format (800 chars, metadata)
- [ ] ⏳ Re-chunk documents with better overlap
- [ ] ⏳ Add metadata filtering by document type
- [ ] ⏳ Create terminology glossary
- [ ] ⏳ Improve embeddings (larger model or fine-tuning)
- [ ] ⏳ Add query classification
- [ ] ⏳ Create accuracy test suite
- [ ] ⏳ Set up monitoring dashboard

## Next Steps

1. **Test Current Improvements** (TODAY)
   ```bash
   python test_format_decision.py
   # Check if responses are more accurate and specific
   ```

2. **Add Missing Documents** (HIGH PRIORITY)
   - You mentioned "we will add those documents as well"
   - Ensure all NEO technical manuals, SOPs, guides are ingested
   ```bash
   python ingest_proposals.py --directory /path/to/new/docs
   ```

3. **Create Glossary** (THIS WEEK)
   - Extract key terms from documents
   - Define each term with document reference
   - Integrate into context retrieval

4. **Re-chunk Documents** (THIS WEEK)
   - Analyze current chunk distribution
   - Adjust chunk size and overlap
   - Re-ingest with better chunking

5. **Monitor & Iterate** (ONGOING)
   - Collect user feedback
   - Analyze failed queries
   - Continuously improve

## Contact for Help

If responses are still not accurate after these improvements:

1. Check which documents are being retrieved:
   - Look for `📚 Retrieved X documents` in logs
   - Verify relevance scores are > 0.70

2. Examine the context being sent to agents:
   - Log the full `rag_context` variable
   - Verify it contains information needed to answer

3. Review agent responses:
   - Check if Response Agent followed rules
   - See if Verification Agent caught issues

4. Adjust thresholds:
   - Increase `min_similarity` to 0.35 or 0.40 for higher quality
   - Increase `top_k` to 20 for more context
   - Increase context chars to 1000 per document

---

**Remember**: The key to accuracy is:
1. **Better document retrieval** (query expansion + metadata)
2. **Stricter prompting** (anti-hallucination rules)
3. **Verification** (catch and fix issues)
4. **Monitoring** (continuous improvement)
