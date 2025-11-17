# Installing C++ Build Tools for Local LLM

## Why Do You Need This?
`llama-cpp-python` requires C++ compiler to build the native extensions that run the local LLM models efficiently.

## Option 1: Quick Install (Recommended)

### Download & Install Visual Studio Build Tools:

1. **Download**: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022

2. **Run the installer** (`vs_BuildTools.exe`)

3. **Select "Desktop development with C++"** workload
   - This includes:
     - MSVC v143 (or latest)
     - Windows 10/11 SDK
     - CMake tools

4. **Install size**: ~7 GB

5. **Installation time**: 10-15 minutes

### After Installation:

```powershell
# Restart PowerShell, then install llama-cpp-python
C:/Users/Balmukund.Mishra/Desktop/NEO/association_mining_system/venv/Scripts/pip.exe install llama-cpp-python
```

---

## Option 2: Use Pre-built Wheels (Faster, No Compiler Needed)

Instead of building from source, use pre-compiled binaries:

```powershell
# Install from pre-built wheels repository
C:/Users/Balmukund.Mishra/Desktop/NEO/association_mining_system/venv/Scripts/pip.exe install llama-cpp-python --prefer-binary --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
```

**Note**: Pre-built wheels might not be available for Python 3.13 yet. If this fails, use Option 1.

---

## Option 3: Alternative - Use Ollama (Easiest)

If you want to avoid compilation, use Ollama which provides ready-to-use local LLMs:

1. Download Ollama: https://ollama.ai/download
2. Install and run: `ollama run phi`
3. Update your code to use Ollama API instead of llama-cpp-python

---

## Verification After Installation:

```powershell
# Test if llama-cpp-python installs successfully
C:/Users/Balmukund.Mishra/Desktop/NEO/association_mining_system/venv/Scripts/pip.exe install llama-cpp-python

# Test the local LLM
C:/Users/Balmukund.Mishra/Desktop/NEO/association_mining_system/venv/Scripts/python.exe setup_local_llm.py --test phi-2-2.7b
```

---

## Current Status:

✅ Models downloaded (Phi-2: 1.4 GB, TinyLlama: 101 MB)
✅ Fallback system working (mock mode)
✅ Configuration ready
⏳ Waiting for llama-cpp-python installation

---

## Quick Decision Matrix:

| Option | Time | Disk Space | Difficulty | Recommendation |
|--------|------|------------|------------|----------------|
| **VS Build Tools** | 15 min | 7 GB | Easy | ⭐ Best for production |
| **Pre-built wheels** | 2 min | 100 MB | Very Easy | ⭐⭐ Try this first! |
| **Ollama** | 5 min | 2 GB | Very Easy | Good alternative |

**My recommendation**: Try Option 2 first (pre-built wheels). If that fails due to Python 3.13, go with Option 1.
