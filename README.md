# Association Mining System# Association Mining System



A comprehensive warehouse analytics platform combining association rule mining with AI-powered insights for NEO warehouse management systems.Warehouse intelligence platform for order pattern analysis and inventory optimization.



## Overview## What it does



This system analyzes SKU relationships and provides intelligent recommendations through:This system helps you analyze your warehouse order data to:

- Market basket analysis for SKU associations- Find patterns in customer orders

- AI chatbot for technical documentation queries- Get AI-powered inventory recommendations  

- Velocity analysis for bin optimization- See demand forecasts and trends

- Real-time performance monitoring- Optimize SKU performance



## Features## Requirements



### Association Mining- Python 3.8 or newer

- FP-Growth algorithm for efficient pattern discovery- MySQL 8.0 or newer

- Configurable support, confidence, and lift thresholds- At least 4GB RAM

- Interactive web dashboard for rule visualization

- Scheduled mining with automatic database updates## Installation



### AI Chatbot1. Download or clone the project

- Technical documentation Q&A using RAG (Retrieval-Augmented Generation)2. Open command prompt and go to the project folder:

- Supports 164 technical documents (proposals, manuals, SOPs)   ```

- Vision capability for flowchart and diagram understanding   cd association_mining_system

- Powered by Groq LLM with HuggingFace embeddings   ```



### Velocity Analysis3. Create a virtual environment:

- ABC classification for inventory prioritization   ```

- Bin allocation optimization recommendations   python -m venv .venv

- Historical trend analysis   ```



### Performance Monitoring4. Activate the virtual environment:

- Real-time mining execution tracking   ```

- Resource usage analytics   .venv\Scripts\activate

- Historical performance logs   ```



## Quick Start5. Install required packages:

   ```

### Prerequisites   pip install -r requirements.txt

- Python 3.10 or higher   ```

- MySQL database

- Windows OS (for batch scripts)## How to run



### Installation### Easy way (recommended)

```

1. Clone the repositorypython main.py

2. Create virtual environment:```

   ```bash

   python -m venv venv### Using batch files (Windows only)

   ``````

quick_start.bat

3. Activate environment:```

   ```bash

   venv\Scripts\activate## How to use

   ```

1. Start the system using one of the methods above

4. Install dependencies:2. Open your web browser

   ```bash3. Go to: http://localhost:5000

   pip install -r requirements.txt4. Set up your database connection

   ```5. Upload your order data

6. Run the analysis

5. Configure environment variables in `.env`:7. View results in the dashboard

   ```

   DB_HOST=localhost## Web Interface

   DB_USER=root

   DB_PASSWORD=your_passwordThe main dashboard runs at: http://localhost:5000

   DB_NAME=your_database

   Features:

   GROQ_API_KEY=your_groq_key- Database setup

   HUGGINGFACE_API_KEY=your_hf_key- Data upload and validation

   ```- Start analysis

- View results and charts

### Running the Application- Download reports



**Option 1: Quick Start (Recommended)**## API Interface

```bash

quick_start.batThe API runs at: http://localhost:8001

```

This starts both FastAPI (port 8080) and Flask UI (port 5000) in background mode.Key endpoints:

- `/docs` - See all available API functions

**Option 2: Manual Start**- `/mine` - Start data analysis

```bash- `/recommendations/{item}` - Get recommendations for an item

# Start API server- `/health` - Check if system is working

uvicorn app.main:app --host 0.0.0.0 --port 8080

## Database Setup

# Start UI server (in separate terminal)

python app/web/main.pyYou need these tables in your MySQL database:

```- Order data table (your transaction records)

- SKU master table (product information)

**Stop Servers**

```bashThe system will create a recommendations table automatically.

stop_servers.bat

```## Configuration



## UsageCreate a `.env` file with your settings:

```

### Web InterfaceDB_HOST=localhost

- Main Dashboard: http://localhost:5000DB_USER=your_username

- Association Mining: http://localhost:5000/association-miningDB_PASSWORD=your_password

- AI Chatbot: http://localhost:5000/chatbotDB_NAME=your_database

- Velocity Analysis: http://localhost:5000/velocity-analysisORDER_TABLE=your_order_table_name

SKU_MASTER_TABLE=your_sku_table_name

### API Documentation```

- Interactive API Docs: http://localhost:8080/docs

- OpenAPI Schema: http://localhost:8080/openapi.json## Troubleshooting



### Document Ingestion**Cannot start the system:**

- Make sure Python is installed

To add new technical documents to the chatbot:- Check that MySQL is running

- Activate the virtual environment first

```bash

# Ingest all documents from configured folders**Database connection errors:**

python ingest_unified.py- Verify your database credentials

- Make sure MySQL service is running

# Or ingest specific PDFs- Check if tables exist

python reingest_documents.py

```**Module not found errors:**

- Activate virtual environment: `.venv\Scripts\activate`

### Running Association Mining- Install packages: `pip install -r requirements.txt`



1. Via Web UI:**Port conflicts:**

   - Navigate to Association Mining dashboard- Web interface uses port 5000

   - Set parameters (min_support, min_confidence, min_lift)- API uses port 8001

   - Click "Run Mining"- Make sure these ports are available



2. Via API:## Getting Help

   ```bash

   curl -X POST http://localhost:8080/api/association-mining/run \If you need help:

     -H "Content-Type: application/json" \1. Check the troubleshooting section above

     -d '{"min_support": 0.01, "min_confidence": 0.3, "min_lift": 1.0}'2. Look at the API documentation at http://localhost:8001/docs

   ```3. Check the log files for error messages



3. Via Scheduled Task (runs automatically based on configuration)## Files and Folders



## Project Structure```

association_mining_system/

```├── main.py                 # Start the system

association_mining_system/├── requirements.txt        # Required packages

├── app/├── scripts/               # Batch files for Windows

│   ├── modules/├── app/                   # Main application code

│   │   ├── association_mining/    # Mining algorithms & UI│   ├── main.py           # API backend

│   │   ├── neo_chatbot/           # AI chatbot with RAG│   ├── web/              # Web dashboard

│   │   ├── velocity_analysis/     # ABC analysis & bin optimization│   ├── modules/          # Analysis features

│   │   └── ai_insights/           # Performance analytics│   └── shared/           # Common code

│   ├── shared/└── utils/                # Helper tools

│   │   ├── config/                # Configuration management```

│   │   ├── database/              # Database connections

│   │   └── utils/                 # Shared utilitiesThat's it! The system should work for analyzing your warehouse data and providing insights.
│   ├── web/                       # Flask UI
│   └── main.py                    # FastAPI application
├── docs/                          # Documentation
├── logs/                          # Application logs
├── requirements.txt               # Python dependencies
├── quick_start.bat               # Quick start script
└── stop_servers.bat              # Stop servers script
```

## Configuration

### Association Mining Parameters
Edit in web UI or pass to API:
- `min_support`: Minimum transaction frequency (default: 0.01)
- `min_confidence`: Minimum rule confidence (default: 0.3)
- `min_lift`: Minimum lift value (default: 1.0)
- `max_length`: Maximum items per rule (default: 10)

### Chatbot Configuration
Edit `app/modules/neo_chatbot/services/llm_service.py`:
- LLM model selection
- Embedding model configuration
- Temperature and token limits

### Database Schema
Required tables:
- `sku_master`: SKU information
- `order_details`: Transaction data
- `sku_recommendations`: Mining results
- `sku_velocity_analysis`: Velocity metrics

## API Endpoints

### Association Mining
- `POST /api/association-mining/run` - Execute mining
- `GET /api/association-mining/recommendations` - Get results
- `GET /api/association-mining/status` - Check mining status

### Chatbot
- `POST /api/chatbot/chat` - Send message
- `POST /api/chatbot/ingest` - Upload documents
- `GET /api/chatbot/history` - Get conversation history

### Velocity Analysis
- `POST /api/velocity-analysis/run` - Run ABC analysis
- `GET /api/velocity-analysis/results` - Get analysis results

## Troubleshooting

### Port Already in Use
```bash
# Kill processes on port 5000 and 8080
stop_servers.bat
```

### Database Connection Failed
- Verify MySQL is running
- Check credentials in `.env`
- Ensure database exists

### Chatbot Not Finding Documents
```bash
# Re-ingest documents
python ingest_unified.py
```

### No Association Rules Found
- Lower `min_support` threshold
- Ensure sufficient transaction data
- Check SKU master data integrity

## Performance Tuning

### For Large Datasets (>100K transactions)
- Increase `min_support` to 0.02 or higher
- Use scheduled mining during off-peak hours
- Enable database indexing on ORDER_ID, SKU_ID

### For Better Chatbot Responses
- Add more technical documents
- Use OpenAI embeddings (set OPENAI_API_KEY)
- Increase context window in llm_service.py

## License

Proprietary - Falcon Autotech

## Support

For technical support, contact the development team or refer to documentation in the `docs/` folder.
