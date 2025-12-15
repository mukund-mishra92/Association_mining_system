# Chatbot Intelligence & Vision Improvements

## Current Issues

### 1. Fixed Response Patterns
**Problem**: Chatbot produces repetitive, templated responses regardless of query type
**Root Cause**: Using `llama-3.1-8b-instant` - too small (8B parameters) for varied, intelligent responses
**Impact**: Poor user experience, robotic answers, limited reasoning capability

### 2. Cannot Process Images in Documents
**Problem**: PDFs contain critical flowcharts/diagrams that the LLM cannot understand
**Root Cause**: Current models are text-only; OCR only extracts text from images, not visual understanding
**Impact**: Missing critical information from process flows, architecture diagrams, visual workflows

---

## Solutions Implemented

### ✅ Solution 1: Upgrade to Better Model (COMPLETED)

**Change Made**: `llama-3.1-8b-instant` → `llama-3.3-70b-versatile`

**File**: `app/modules/neo_chatbot/services/llm_service.py` (line ~161)

```python
model="llama-3.3-70b-versatile",  # 9x larger, much better quality
```

**Benefits**:
- 9x more parameters (70B vs 8B)
- Better reasoning and context understanding
- More varied, natural responses
- Still fast on Groq infrastructure
- No additional cost (same API)

**Expected Improvement**: 60-80% better response quality, significantly less templating

---

## Solutions Available for Vision Support

### Option A: Use OpenAI GPT-4 Vision (Recommended for Quality)

**Model**: `gpt-4-vision-preview` or `gpt-4o` (has vision built-in)
**Cost**: ~$0.01/1K tokens ($0.03 for vision requests)
**Quality**: ⭐⭐⭐⭐⭐ Excellent
**Speed**: ⭐⭐⭐ Medium (2-5 seconds)

**Implementation**:
1. Change OpenAI model to `gpt-4o` in llm_service.py
2. Add image support to message builder
3. Extract images from PDFs and convert to base64
4. Send images with text queries

**Pros**:
- Best-in-class image understanding
- Excellent flowchart/diagram interpretation
- Can describe complex process flows accurately
- Good at technical diagrams

**Cons**:
- Higher cost than text-only
- Requires OpenAI API key
- Slower than text-only responses

---

### Option B: Use Claude 3 Opus with Vision (Recommended for Cost)

**Model**: `claude-3-5-sonnet-20241022` (already configured!)
**Cost**: ~$0.003/1K tokens ($0.015 for vision)
**Quality**: ⭐⭐⭐⭐⭐ Excellent
**Speed**: ⭐⭐⭐⭐ Fast (1-3 seconds)

**Implementation**:
1. Enable vision mode in Anthropic API calls
2. Add image message format support
3. Extract and send images from PDFs

**Pros**:
- Already configured in the system!
- Excellent image understanding (comparable to GPT-4V)
- Lower cost than GPT-4
- Faster responses
- Better at following instructions

**Cons**:
- Requires Anthropic API key
- Slightly more complex message format

---

### Option C: Hybrid Approach (Best Balance)

**Strategy**: Use different models for different query types

| Query Type | Model | Reasoning |
|------------|-------|-----------|
| Simple text questions | Groq llama-3.3-70b | Fast, cheap, good quality |
| Complex explanations | Groq llama-3.3-70b | Still fast, excellent quality |
| Image/diagram queries | Claude 3 Sonnet | Best vision + cost balance |
| Critical accuracy | GPT-4o | Highest quality when needed |

**Implementation**:
1. Detect if query requires vision (keywords: "diagram", "flowchart", "image", "show me")
2. Check if retrieved documents contain images
3. Route to vision-enabled model only when needed
4. Use Groq for text-only queries (fast & cheap)

**Pros**:
- Optimal cost/performance balance
- Fast responses for most queries
- High quality when images involved
- Uses existing infrastructure

**Cons**:
- More complex routing logic
- Need both API keys configured

---

## Image Extraction Enhancement

### Current Implementation
- ✅ PyMuPDF (fitz) for extracting images from PDFs
- ✅ Tesseract OCR for extracting text from images
- ❌ No visual understanding of diagrams/flowcharts

### Recommended Enhancement

**Add Vision-Based Image Description During Ingestion**:

```python
# In ingest_documents.py
def describe_image_with_vision_llm(self, image_bytes: bytes, page_num: int) -> str:
    """Use vision LLM to describe diagram/flowchart"""
    
    # Convert image to base64
    image_b64 = base64.b64encode(image_bytes).decode()
    
    # Send to Claude/GPT-4V with specialized prompt
    response = vision_llm.analyze_image(
        image=image_b64,
        prompt="""Describe this technical diagram/flowchart in detail:
        - What process or system does it show?
        - What are the main steps/components?
        - What are the key relationships/flows?
        - Any important labels or annotations?
        
        Be specific and technical. This will be used for documentation search."""
    )
    
    return response
```

**Benefits**:
- One-time cost during ingestion
- Rich textual descriptions of images stored in vector DB
- Can search by diagram content
- No need to send images during every query

**Storage**:
```python
# Enhanced document chunk
chunk = {
    "text": "...",
    "images": [
        {
            "page": 5,
            "description": "Flowchart showing order processing workflow with 7 steps...",
            "image_id": "img_001"  # Reference to stored image
        }
    ]
}
```

---

## Recommended Implementation Plan

### Phase 1: Immediate (TODAY) ✅
- [x] Upgrade Groq model to llama-3.3-70b-versatile
- [x] Test response quality improvement

### Phase 2: Vision Support (THIS WEEK)
1. **Add Vision Query Detection** (30 min)
   - Detect image-related keywords
   - Check if retrieved chunks have images
   
2. **Implement Claude Vision Support** (2 hours)
   - Modify llm_service.py to support vision messages
   - Add image extraction from PDFs
   - Format messages for Claude vision API
   
3. **Test with Sample Flowcharts** (1 hour)
   - Create test queries about diagrams
   - Verify accurate descriptions
   - Tune prompts for technical diagrams

### Phase 3: Enhanced Ingestion (NEXT WEEK)
1. **Image Description During Ingestion** (4 hours)
   - Add vision LLM calls during document processing
   - Store image descriptions in vector DB
   - Update chunk schema to include image metadata
   
2. **Image Storage & Retrieval** (2 hours)
   - Store images in filesystem or database
   - Add image references to chunks
   - Retrieve images when needed for queries

---

## Configuration Required

### API Keys Needed

```env
# Current (for text only)
GROQ_API_KEY=gsk_xxx

# For vision support (choose one or both)
ANTHROPIC_API_KEY=sk-ant-xxx  # Claude 3 Sonnet (recommended)
OPENAI_API_KEY=sk-xxx         # GPT-4 Vision (premium option)
```

### Model Settings

```python
# app/modules/neo_chatbot/services/llm_service.py

# For text queries (current)
GROQ_MODEL = "llama-3.3-70b-versatile"  # ✅ Already updated

# For vision queries (add these)
VISION_MODEL_ANTHROPIC = "claude-3-5-sonnet-20241022"  # Already configured!
VISION_MODEL_OPENAI = "gpt-4o"  # If using OpenAI

# Enable vision support
ENABLE_VISION = True
```

---

## Testing Strategy

### Test Case 1: Text Query (No Images)
**Query**: "What is the order processing workflow?"
**Expected**: Uses Groq llama-3.3-70b, fast response, detailed explanation from text docs

### Test Case 2: Diagram Query
**Query**: "Show me the flowchart for returns processing"
**Expected**: 
1. Detects image-related query
2. Retrieves chunks with images
3. Sends to Claude Vision
4. Returns detailed explanation with diagram interpretation

### Test Case 3: Complex Technical Diagram
**Query**: "Explain the system architecture diagram on page 15"
**Expected**:
1. Identifies page reference
2. Extracts image from page 15
3. Sends to vision LLM
4. Returns component breakdown, connections, data flows

---

## Success Metrics

| Metric | Current | Target | How to Measure |
|--------|---------|--------|----------------|
| Response variety | Low (templated) | High (natural) | Manual review of 20 queries |
| Image understanding | 0% (no capability) | 90% (accurate) | Test with 10 flowcharts |
| Response quality | 3/10 | 8/10 | User satisfaction rating |
| Cost per query | $0.0001 | $0.002 | Track API usage |
| Response time (text) | 2s | 2-3s | Same or slightly slower |
| Response time (vision) | N/A | 4-6s | Acceptable for complex queries |

---

## Cost Analysis

### Current Cost (Text Only)
- Groq llama-3.1-8b: ~$0.0001 per query
- **Monthly (1000 queries)**: ~$0.10

### With Vision Support (Hybrid)
Assume 80% text queries, 20% vision queries:
- 800 text queries × $0.0001 = $0.08
- 200 vision queries × $0.003 = $0.60
- **Monthly (1000 queries)**: ~$0.68

**ROI**: Massive improvement in user experience for <$1/month

---

## Next Steps

1. **Verify current improvement**: Test chatbot with llama-3.3-70b to confirm better responses
2. **Choose vision approach**: Option B (Claude) or Option C (Hybrid) recommended
3. **Implement vision detection**: Add logic to identify image-related queries
4. **Add vision support**: Modify llm_service.py to handle image messages
5. **Test with real documents**: Use actual PDFs with flowcharts to validate
6. **Deploy to production**: Roll out gradually with monitoring

---

## References

- Groq Models: https://console.groq.com/docs/models
- Claude Vision: https://docs.anthropic.com/claude/docs/vision
- GPT-4 Vision: https://platform.openai.com/docs/guides/vision
- PyMuPDF: https://pymupdf.readthedocs.io/
