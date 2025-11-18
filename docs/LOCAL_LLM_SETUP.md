# Local LLM Fallback - Setup Guide

## Overview

The NEO Chatbot now supports **automatic fallback to local LLM** when Groq API (or other cloud APIs) are unavailable. This ensures the system remains operational even without internet connectivity or during API outages.

---

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    User Query                               │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│              Try Groq API (Primary)                         │
│              llama-3.3-70b-versatile                        │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
   ✅ Success            ❌ API Error
        │                     │
        │                     ▼
        │          ┌─────────────────────────────┐
        │          │   Automatic Fallback to     │
        │          │   Local LLM (Phi-2 2.7B)    │
        │          └──────────┬──────────────────┘
        │                     │
        │              ┌──────┴──────┐
        │              │             │
        │         ✅ Success    ❌ Error
        │              │             │
        └──────────────┼─────────────┘
                       │
                       ▼
           ┌──────────────────────┐
           │  Return Response     │
           └──────────────────────┘
```

---

## Quick Setup (Recommended)

### Option 1: Interactive Setup (Easiest)

```bash
# Install required package
pip install llama-cpp-python huggingface-hub

# Run setup wizard
python setup_local_llm.py --setup
```

This will:
1. Download Phi-2 2.7B model (1.56 GB)
2. Test the model with sample queries
3. Configure .env automatically
4. Enable fallback system

### Option 2: Manual Setup

1. **Install dependencies:**
   ```bash
   pip install llama-cpp-python huggingface-hub
   ```

2. **Download model:**
   ```bash
   python setup_local_llm.py --download phi-2-2.7b
   ```

3. **Update .env:**
   ```bash
   # Add these lines to .env
   LOCAL_LLM_ENABLED=true
   LOCAL_LLM_MODEL=phi-2-2.7b
   ```

4. **Restart server:**
   ```bash
   python app/web/main.py
   ```

---

## Available Models

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| **TinyLlama 1.1B** | 669 MB | ⚡⚡⚡ Fast | ⭐⭐ Basic | Simple queries, low-resource systems |
| **Phi-2 2.7B** ⭐ | 1.56 GB | ⚡⚡ Moderate | ⭐⭐⭐ Good | **Recommended** - Balanced speed/quality |
| **Mistral 7B** | 4.37 GB | ⚡ Slower | ⭐⭐⭐⭐ High | High-quality responses, good hardware |

**⭐ = Recommended** for most users

---

## System Requirements

### Minimum (TinyLlama 1.1B):
- RAM: 2 GB free
- Disk: 1 GB free
- CPU: Any modern processor

### Recommended (Phi-2 2.7B):
- RAM: 4 GB free
- Disk: 2 GB free
- CPU: 4+ cores

### High-Performance (Mistral 7B):
- RAM: 8 GB free
- Disk: 5 GB free
- CPU: 8+ cores or GPU

---

## Usage Examples

### 1. Download and Test Model

```bash
# List available models
python setup_local_llm.py --list

# Download specific model
python setup_local_llm.py --download phi-2-2.7b

# Test model
python setup_local_llm.py --test phi-2-2.7b
```

### 2. Interactive Menu

```bash
python setup_local_llm.py --interactive
```

Menu options:
1. List available models
2. Download model
3. Test model
4. Quick setup (Phi-2)
5. Exit

### 3. Programmatic Usage

```python
from app.modules.neo_chatbot.services.local_llm_service import get_local_llm

# Get LLM instance
llm = get_local_llm(model_name="phi-2-2.7b")

# Generate response
response = llm.chat(
    messages=[
        {"role": "system", "content": "You are a SQL expert."},
        {"role": "user", "content": "Show me all active bots"}
    ],
    max_tokens=500,
    temperature=0.3
)

print(response)
```

---

## Configuration Options

Add these to your `.env` file:

```bash
# Enable local LLM fallback
LOCAL_LLM_ENABLED=true

# Choose model (tinyllama-1.1b, phi-2-2.7b, mistral-7b-instruct)
LOCAL_LLM_MODEL=phi-2-2.7b

# Maximum tokens to generate
LOCAL_LLM_MAX_TOKENS=500

# Temperature (0.0-1.0, lower = more deterministic)
LOCAL_LLM_TEMPERATURE=0.3
```

---

## How Fallback Works

### Scenario 1: Normal Operation (Groq API Available)

```
User: "Show me all active bots"
  ↓
System: Try Groq API
  ↓
Groq: ✅ Success → Returns response
  ↓
User sees response (fast, high quality)
```

### Scenario 2: API Failure (Groq Down)

```
User: "Show me all active bots"
  ↓
System: Try Groq API
  ↓
Groq: ❌ Connection Error / Rate Limit / Timeout
  ↓
System: "Groq failed, switching to local LLM..."
  ↓
Local LLM (Phi-2): ✅ Success → Returns response
  ↓
User sees response (slower but system stays online)
```

### Scenario 3: No Groq API Key (Local Only)

```
User: "Show me all active bots"
  ↓
System: No Groq API key configured
  ↓
Local LLM (Phi-2): ✅ Used directly
  ↓
User sees response (works offline!)
```

---

## Performance Comparison

| Metric | Groq API | Phi-2 Local | TinyLlama Local |
|--------|----------|-------------|-----------------|
| **Response Time** | 1-2 seconds | 3-8 seconds | 2-5 seconds |
| **Quality** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Cost** | API usage | Free | Free |
| **Offline** | ❌ No | ✅ Yes | ✅ Yes |
| **First Query** | Fast | Slow (load model) | Moderate |
| **Subsequent** | Fast | Fast (cached) | Fast (cached) |

---

## Testing Fallback

### Test 1: Simulate Groq API Failure

```bash
# Temporarily remove Groq API key
# In .env, comment out:
# GROQ_API_KEY=...

# Restart server
python app/web/main.py

# Ask chatbot a question
# System should automatically use local LLM
```

### Test 2: Verify Logs

```
# Look for these log messages:

✅ Success (Groq available):
   "✅ Groq (Fast Inference) LLM initialized"
   "🚀 Generating with Groq..."

✅ Success (Fallback to local):
   "❌ Error with groq LLM: ..."
   "🔄 Attempting fallback to local LLM..."
   "💾 Using local LLM: phi-2-2.7b"
   "💭 Generating with local LLM..."
```

### Test 3: Verify Response Quality

Ask test questions:
1. **SQL Query**: "Show me all bots from bot_master table"
2. **Knowledge Base**: "What is an ASRS system?"
3. **Diagnostic**: "Robot not picking items"

Compare responses:
- Groq: High quality, detailed, fast
- Local LLM: Good quality, adequate detail, slower

---

## Troubleshooting

### Issue: "llama-cpp-python not installed"

**Solution:**
```bash
pip install llama-cpp-python
```

If this fails, try with specific version:
```bash
pip install llama-cpp-python==0.2.20
```

### Issue: "Failed to download model"

**Solution:**
- Check internet connection
- Ensure ~2 GB free disk space
- Try again (downloads can resume)
- Manual download:
  ```bash
  # Download from HuggingFace directly
  # URL in error message or check local_llm_service.py AVAILABLE_MODELS
  ```

### Issue: "Model loading failed"

**Solution:**
- Check RAM (need 4+ GB free for Phi-2)
- Try smaller model (TinyLlama)
- Close other applications
- Restart Python process

### Issue: "Responses are slow"

**Solution:**
- This is normal for local LLM (3-8 seconds)
- Subsequent queries faster (model cached in memory)
- Use smaller model (TinyLlama) for speed
- Reduce max_tokens in config

### Issue: "Low quality responses"

**Solution:**
- Use larger model (Mistral 7B instead of TinyLlama)
- Increase temperature for creativity
- Adjust prompts in service files
- Groq API gives better quality (use as primary)

---

## Model Storage Location

Models are downloaded to:
```
app/modules/neo_chatbot/data/models/
├── tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf          (669 MB)
├── phi-2.Q4_K_M.gguf                              (1.56 GB)
└── mistral-7b-instruct-v0.2.Q4_K_M.gguf          (4.37 GB)
```

To free space, delete unused models:
```bash
rm app/modules/neo_chatbot/data/models/*.gguf
```

---

## Advanced Configuration

### Use GPU Acceleration (if available)

Edit `local_llm_service.py`:
```python
self.llm = Llama(
    model_path=str(model_path),
    n_ctx=2048,
    n_threads=4,
    n_gpu_layers=35,  # Change from 0 to 35 (use GPU)
    verbose=False
)
```

Requires:
- NVIDIA GPU with CUDA
- `pip install llama-cpp-python[cuda]`

### Custom Model

Add to `local_llm_service.py` `AVAILABLE_MODELS`:
```python
"custom-model": {
    "url": "https://huggingface.co/.../model.gguf",
    "filename": "model.gguf",
    "size_mb": 1000,
    "description": "Custom model description"
}
```

---

## Best Practices

### 1. Model Selection

- **Production**: Use Phi-2 (good balance)
- **Development**: Use TinyLlama (faster iteration)
- **High-Quality**: Use Mistral 7B (if hardware allows)

### 2. Fallback Strategy

```
Primary: Groq API (fast, high quality, requires internet)
Fallback: Local LLM (slower, good quality, works offline)
```

### 3. Memory Management

- Local LLM stays in memory after first use
- Restart server to free memory
- Use smaller models if RAM limited

### 4. Response Optimization

For local LLM, use shorter prompts:
- Remove unnecessary context
- Use lower max_tokens (200-500)
- Set temperature lower (0.2-0.3)

---

## Security Considerations

✅ **Advantages of Local LLM:**
- Data never leaves your server
- No API keys to manage
- No rate limits
- Works offline

⚠️ **Considerations:**
- Models are publicly available (not proprietary)
- Quality lower than GPT-4/Claude
- Requires local compute resources

---

## Migration Guide

### From Cloud-Only to Hybrid

**Before:**
```env
GROQ_API_KEY=your_api_key
```

**After:**
```env
GROQ_API_KEY=your_api_key  # Primary
LOCAL_LLM_ENABLED=true     # Fallback
LOCAL_LLM_MODEL=phi-2-2.7b
```

**No code changes required!** The system automatically falls back.

---

## FAQ

**Q: Will this slow down my system?**
A: Model loading takes 5-10 seconds initially, then stays in memory. Only affects queries when Groq fails.

**Q: Can I use multiple models?**
A: Yes, but only one loaded at a time. Change `LOCAL_LLM_MODEL` in .env and restart.

**Q: Does this work on Windows/Mac/Linux?**
A: Yes, llama-cpp-python supports all platforms.

**Q: Can I use this without Groq API?**
A: Yes! Don't set GROQ_API_KEY and system will use local LLM by default.

**Q: How do I update models?**
A: Delete old .gguf file and re-run download. New versions released on HuggingFace.

---

## Support

For issues:
1. Check logs: `logs/chatbot.log`
2. Run tests: `python setup_local_llm.py --test phi-2-2.7b`
3. Verify config: Check .env file
4. Review this guide

---

## Summary

✅ **Implemented:**
- Local LLM service with 3 model options
- Automatic fallback when Groq API fails
- Download utility with interactive menu
- Configuration via .env
- Comprehensive error handling

✅ **Benefits:**
- System stays online during API outages
- Works completely offline
- No data leaves your server
- Free (no API costs for fallback)

✅ **Next Steps:**
1. Run: `python setup_local_llm.py --setup`
2. Test: Ask chatbot questions
3. Verify: Check logs for fallback behavior
4. Optimize: Choose model based on your hardware

**The chatbot is now resilient to API failures!** 🚀
