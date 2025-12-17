# Association Mining System

**NEO Warehouse Intelligence Platform**  
AI-powered analytics for order patterns, inventory optimization, and intelligent support.

---

## 🎯 What It Does

This system analyzes warehouse order data to provide:

- **📊 Association Mining** - Discover SKU relationships and bundling opportunities
- **🤖 AI Chatbot Support** - Three specialized assistants:
  - 💬 General Chatbot - Technical documentation Q&A
  - 🔧 Diagnostic Support - Troubleshoot warehouse issues
  - 📊 SQL Assistant - Natural language database queries
- **📈 Velocity Analysis** - Optimize bin placement based on demand
- **🎯 Smart Recommendations** - Data-driven inventory decisions

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- MySQL 8.0+
- 4GB RAM minimum

### Installation

1. **Clone the repository**
   ```bash
   cd association_mining_system
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment**
   - Copy `.env.example` to `.env`
   - Add your database credentials and API keys:
     ```
     DB_HOST=localhost
     DB_USER=your_user
     DB_PASSWORD=your_password
     DB_NAME=neo_database
     
     GROQ_API_KEY=your_groq_key
     HUGGINGFACE_API_KEY=your_hf_key
     ```

4. **Ingest documents (first-time setup)**
   ```bash
   python ingest_unified.py
   ```

5. **Start the servers**
   
   **Option A - Visible Windows** (recommended for development):
   ```bash
   python quick_start.py
   ```
   
   **Option B - Background** (silent mode):
   ```bash
   python start_background.py
   ```

6. **Access the application**
   - 🌐 Web UI: http://localhost:5000
   - 🚀 FastAPI: http://localhost:8080
   - 📚 API Docs: http://localhost:8080/docs

---

## 📁 Project Structure

```
association_mining_system/
├── app/
│   ├── modules/
│   │   ├── association_mining/    # Mining engine
│   │   └── neo_chatbot/            # AI chatbot services
│   ├── web/                        # Flask UI
│   └── main.py                     # FastAPI backend
├── docs/                           # Documentation
├── logs/                           # Application logs
├── templates/                      # UI templates
├── quick_start.py                  # Start servers (visible)
├── start_background.py             # Start servers (background)
├── ingest_unified.py               # Document ingestion
├── ingestion_config.py             # Ingestion settings
├── requirements.txt                # Dependencies
├── .env                            # Configuration (create from .env.example)
└── README.md                       # This file
```

---

## 🎨 Features

### 1. Association Mining
- **FP-Growth Algorithm** for efficient pattern discovery
- **Configurable Parameters**:
  - Support: Minimum frequency threshold
  - Confidence: Rule strength
  - Lift: Correlation measure
- **Interactive Dashboard** for rule visualization
- **Scheduled Mining** with automatic updates

### 2. AI Chatbot System

#### 💬 General Chatbot
- Technical documentation Q&A using RAG
- Supports 160+ documents (proposals, manuals, SOPs)
- Vision capability for diagrams/flowcharts
- Powered by Groq LLM + HuggingFace embeddings

#### 🔧 Diagnostic Support
- Real-time troubleshooting for warehouse issues
- SQL query execution for system diagnostics
- Historical issue database with 30+ known solutions
- Intelligent root cause analysis

#### 📊 SQL Assistant
- Natural language to SQL conversion
- Safe query execution with validation
- Conversational query refinement
- Schema learning and optimization

### 3. Velocity Analysis
- Demand pattern tracking
- Bin optimization recommendations
- SKU performance metrics

---

## 🛠️ Usage

### Running Association Mining

1. Configure parameters in the web UI
2. Select date range for analysis
3. Click "Start Mining"
4. View results in the Rules Dashboard

### Using AI Chatbot

1. Open http://localhost:5000
2. Select chatbot type:
   - **General** - Ask about documentation
   - **Diagnostic** - Troubleshoot issues
   - **SQL** - Query database
3. Type your question
4. Get intelligent, context-aware responses

### Document Ingestion

To update the knowledge base:
```bash
python ingest_unified.py
```

Configuration in `ingestion_config.py`:
- Document paths
- Chunk sizes
- Embedding models
- Vector store settings

---

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=neo_database

# API Keys
GROQ_API_KEY=your_groq_api_key
HUGGINGFACE_API_KEY=your_hf_api_key

# Logging
LOG_LEVEL=INFO
```

### Mining Parameters

Edit in web UI or `app/modules/association_mining/config.py`:
- `min_support`: 0.001 - 0.1 (default: 0.01)
- `min_confidence`: 0.3 - 0.9 (default: 0.5)
- `min_lift`: 1.0 - 10.0 (default: 1.5)

---

## 📊 API Endpoints

### Association Mining
- `POST /api/association-mining/run` - Start mining
- `GET /api/association-mining/rules` - Get rules
- `GET /api/association-mining/status` - Check status

### Chatbot
- `POST /api/chat` - Send message
- `GET /api/chat/history` - Get conversation
- `POST /api/chat/feedback` - Submit feedback

### Diagnostics
- `POST /api/diagnostic/search` - Search issues
- `GET /api/diagnostic/issues` - List all issues
- `POST /api/diagnostic/query` - Run diagnostic

Full API documentation: http://localhost:8080/docs

---

## 🐛 Troubleshooting

### Servers won't start
- Check if ports 5000 and 8080 are available
- Verify virtual environment is activated
- Check `.env` file exists and is configured

### Database connection errors
- Verify MySQL is running
- Check credentials in `.env`
- Ensure database exists

### Chatbot not responding
- Verify API keys in `.env`
- Check internet connection
- Review logs in `logs/` folder

### Document ingestion fails
- Ensure document paths exist in `ingestion_config.py`
- Check file permissions
- Verify sufficient disk space

---

## 📝 Logs

Application logs are stored in:
- `logs/association_mining.log` - Mining operations
- `logs/neo_chatbot.log` - Chatbot activity
- `logs/fastapi_background.log` - FastAPI server
- `logs/flask_background.log` - Flask UI server

---

## 🔄 Updates & Maintenance

### Updating Documents
```bash
python ingest_unified.py
```

### Clearing Cache
```bash
# Remove vector store cache
rm -rf app/modules/neo_chatbot/data/vector_store/*
```

### Database Backup
Regularly backup your MySQL database:
```bash
mysqldump -u user -p neo_database > backup.sql
```

---

## 🤝 Support

For issues or questions:
1. Check logs in `logs/` folder
2. Review documentation in `docs/`
3. Use Diagnostic Support chatbot
4. Contact system administrator

---

## 📄 License

Internal use only - NEO Warehouse Management System

---

## 🎯 Quick Commands

| Action | Command |
|--------|---------|
| Start (visible) | `python quick_start.py` |
| Start (background) | `python start_background.py` |
| Ingest documents | `python ingest_unified.py` |
| Activate venv | `venv\Scripts\activate` |
| Install deps | `pip install -r requirements.txt` |
| View API docs | http://localhost:8080/docs |
| Access UI | http://localhost:5000 |

---

**Version**: 2.0  
**Last Updated**: December 2025
