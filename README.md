# Association Mining System 🔗

A comprehensive data mining platform for analyzing customer purchase patterns and SKU performance. Built with Flask, FastAPI, and MySQL.

## ✨ New Features

� **Windows Service Support** - Run the system as a background Windows service with auto-restart capabilities  
🔑 **Primary Keys on All Tables** - Enhanced database integrity with proper primary keys on all tables  
📊 **Scheduler Service** - Automated mining jobs with configurable schedules  
🔄 **Auto-Recovery** - Automatic process restart on failures  

**📖 See [SERVICE_SETUP.md](SERVICE_SETUP.md) for complete setup instructions**

## 🏗️ Project Structure

A production-ready association rule mining system with FastAPI backend for analyzing customer purchase patterns and generating item recommendations.



```

association_mining_system/

├── main.py                 # Main entry point## 🏗️ Project Structure## Features

├── requirements.txt        # Python dependencies

├── scripts/               # Startup scripts

│   ├── start.bat

│   ├── quick_start.bat```- **Enhanced time-weighted association rule mining** using FP-Growth algorithm

│   └── start_system.bat

├── app/                   # Main applicationassociation_mining_system/- **Multiple time-based modeling approaches** including seasonal patterns, trend analysis, and RFM-style weighting

│   ├── main.py           # FastAPI backend entry point

│   ├── shared/           # Shared components├── main.py                 # Main entry point- **Temporal stability and trend analysis** for more robust recommendations

│   │   ├── config/       # Configuration management

│   │   ├── database/     # Database connections├── requirements.txt        # Python dependencies- **Multiple scoring methods** for ranking recommendations with temporal factors

│   │   └── utils/        # Shared utilities

│   ├── modules/          # Feature modules├── scripts/               # Startup scripts- **FastAPI REST API** with background task processing

│   │   ├── association_mining/  # Association rule mining

│   │   │   ├── api/      # API endpoints│   ├── start.bat- **MySQL database integration** with configurable table names

│   │   │   ├── services/ # Business logic

│   │   │   └── models/   # Data models│   ├── quick_start.bat- **Configurable parameters** via environment variables

│   │   └── sku_analysis/ # SKU performance analysis

│   └── web/              # Web interface│   └── start_system.bat- **Production-ready logging** and error handling

│       └── main.py       # Flask UI application

├── utils/                # Development utilities├── app/                   # Main application

│   ├── database/         # Database tools

│   └── testing/          # Test utilities│   ├── main.py           # FastAPI backend entry point## Project Structure

└── docs/                 # Documentation

```│   ├── shared/           # Shared components



## 🚀 Quick Start│   │   ├── config/       # Configuration management```



### Prerequisites│   │   ├── database/     # Database connectionsassociation_mining_system/

- **Python 3.8+** installed on your system

- **Virtual Environment** (.venv) set up with dependencies│   │   └── utils/        # Shared utilities├── app/

- **MySQL 8.0+** database server running

│   ├── modules/          # Feature modules│   ├── __init__.py

### Setup Instructions

```bash│   │   ├── association_mining/  # Association rule mining│   ├── main.py              # FastAPI server

# 1. Clone/download the project

cd association_mining_system│   │   │   ├── api/      # API endpoints│   ├── database/



# 2. Create and activate virtual environment│   │   │   ├── services/ # Business logic│   │   ├── __init__.py

python -m venv .venv

.venv\Scripts\activate  # Windows│   │   │   └── models/   # Data models│   │   └── connection.py    # Database connection

source .venv/bin/activate  # Linux/Mac

│   │   └── sku_analysis/ # SKU performance analysis│   ├── services/

# 3. Install dependencies

pip install -r requirements.txt│   └── web/              # Web interface│   │   ├── __init__.py

```

│       └── main.py       # Flask UI application│   │   ├── mining_service.py # Association rule mining logic

### Option 1: Use Main Entry Point (Recommended)

```bash├── utils/                # Development utilities│   │   └── scoring_service.py # Scoring algorithms

# Start web interface only (uses virtual environment automatically)

.venv\Scripts\python.exe main.py│   ├── database/         # Database tools│   ├── api/



# Start FastAPI backend only  │   └── testing/          # Test utilities│   │   ├── __init__.py

.venv\Scripts\python.exe main.py api

└── docs/                 # Documentation│   │   └── endpoints.py     # API endpoints

# Start all services

.venv\Scripts\python.exe main.py all```│   └── utils/

```

│       ├── __init__.py

### Option 2: Use Batch Scripts (Auto-detects Virtual Environment)

```bash## 🚀 Quick Start│       └── config.py        # Configuration

# Quick start (web interface) - automatically uses .venv if available

scripts\quick_start.bat├── requirements.txt



# Start complete system - automatically uses .venv if available### Option 1: Use Main Entry Point (Recommended)├── .env

scripts\start_system.bat

``````bash└── README.md



### Option 3: Manual Start (Advanced)# Start web interface only```

```bash

# Web Interface (Flask) - use virtual environmentpython main.py

.venv\Scripts\python.exe -m app.web.main

## Setup Instructions

# API Backend (FastAPI) - use virtual environment

.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload# Start FastAPI backend only  

```

python main.py api### 1. Install Dependencies

## 🌟 Features



### 🔗 Association Rule Mining

- **Apriori Algorithm Implementation**: Find frequent itemsets and association rules# Start all services```bash

- **Interactive Web Interface**: Easy-to-use UI for configuration and analysis

- **Real-time Progress Tracking**: Monitor mining progress with detailed logspython main.py allcd association_mining_system

- **Flexible Database Configuration**: Support for multiple database configurations

- **Rule Quality Metrics**: Support, confidence, and lift calculations```pip install -r requirements.txt

- **Export Capabilities**: Download results in various formats

```

### 📊 SKU Analysis (Coming Soon)

- **Fast/Slow Moving Analysis**: Identify product velocity patterns### Option 2: Use Batch Scripts

- **Inventory Optimization**: Data-driven recommendations

- **Performance Dashboards**: Visual analytics and insights```bash### 2. Configure Environment

- **Trend Analysis**: Historical performance tracking

# Quick start (web interface)

## 🔧 Configuration

scripts\quick_start.batUpdate the `.env` file with your database credentials:

### Database Setup

1. **Configure through Web Interface**: Use the intuitive UI at http://localhost:5000

2. **Environment Variables**: Set up `.env` file for default configuration

3. **Dynamic Configuration**: Change settings without restarting the application# Start complete system```env



### Required Database Tablesscripts\start_system.batDB_HOST=localhost

- `order_table`: Customer order records

- `table_sku`: Product SKU information```DB_USER=root



## 📡 API EndpointsDB_PASSWORD=root



### Association Mining API (Port 8001)### Option 3: Manual StartDB_NAME=neo

- `GET /docs` - Interactive API documentation

- `POST /mine` - Start association rule mining```bashMIN_SUPPORT=0.05

- `GET /status/{task_id}` - Check mining progress

- `GET /results/{task_id}` - Retrieve mining results# Web Interface (Flask)MIN_CONFIDENCE=0.3



### Web Interface (Port 5000)python -m app.web.mainMIN_LIFT=1.0

- `/` - Main dashboard and database configuration

- `/start-mining` - Begin association rule miningMAX_RECOMMENDATIONS=10

- `/view-results` - View and analyze results

# API Backend (FastAPI)  DECAY_RATE=0.05

## 🛠️ Development

python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload```

### Setting Up Development Environment

```bash```

# Clone and enter directory

cd association_mining_system### 3. Run the Server



# Create virtual environment## 🌟 Features

python -m venv .venv

<!-- ```bash

# Activate virtual environment

.venv\Scripts\activate  # Windows### 🔗 Association Rule Mininguvicorn app.main:app --reload --host 0.0.0.0 --port 8000

source .venv/bin/activate  # Linux/Mac

- **Apriori Algorithm Implementation**: Find frequent itemsets and association rules``` -->

# Install dependencies

pip install -r requirements.txt- **Interactive Web Interface**: Easy-to-use UI for configuration and analysis

```

- **Real-time Progress Tracking**: Monitor mining progress with detailed logscd "C:\Users\Balmukund.Mishra\Desktop\NEO\association_mining_system"

### Project Architecture

- **Flexible Database Configuration**: Support for multiple database configurationspy -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

#### Modular Design

- **app/shared/**: Common components used across features- **Rule Quality Metrics**: Support, confidence, and lift calculations

- **app/modules/**: Individual feature modules with their own API, services, and models

- **app/web/**: Web interface for user interaction- **Export Capabilities**: Download results in various formatsThe API will be available at: `http://localhost:8000`

- **utils/**: Development and testing utilities



#### Key Components

- **Configuration Management**: Centralized config handling in `app/shared/config/`### 📊 SKU Analysis (Coming Soon)API Documentation: `http://localhost:8000/docs`

- **Database Layer**: Reusable connection management in `app/shared/database/`

- **Task Management**: Background task tracking in `app/shared/utils/`- **Fast/Slow Moving Analysis**: Identify product velocity patterns

- **Service Layer**: Business logic encapsulation in feature-specific services

- **Inventory Optimization**: Data-driven recommendations## API Endpoints

### Adding New Features

1. Create new module in `app/modules/`- **Performance Dashboards**: Visual analytics and insights

2. Implement API endpoints, services, and models

3. Add module routes to main FastAPI application- **Trend Analysis**: Historical performance tracking### 1. Start Mining Process

4. Update documentation and tests



## 🧪 Testing

## 🔧 Configuration**POST** `/api/v1/mine-rules`

### Run Tests

```bash

# Run all tests

python -m pytest utils/testing/### Database Setup```json



# Run specific test1. **Configure through Web Interface**: Use the intuitive UI at http://localhost:5000{

.venv\Scripts\python.exe utils/testing/test_pymysql_fix.py

2. **Environment Variables**: Set up `.env` file for default configuration  "days_back": 30,

# Test project structure

.venv\Scripts\python.exe utils/testing/test_structure.py3. **Dynamic Configuration**: Change settings without restarting the application  "use_enhanced_mining": true,

```

  "time_weighting_method": "exponential_decay",

### Database Utilities

```bash### Required Database Tables  "time_segmentation": "weekly"

# Check database connection

.venv\Scripts\python.exe utils/database/check_table.py- `order_table`: Customer order records}



# Diagnose data quality- `table_sku`: Product SKU information```

.venv\Scripts\python.exe utils/database/diagnose_data.py



# Test table joins

.venv\Scripts\python.exe utils/database/check_join.py## 📡 API Endpoints**Time Weighting Methods:**

```

- `exponential_decay`: Recent transactions weighted higher (default)

## 📋 Requirements

### Association Mining API (Port 8001)- `linear_decay`: Linear decrease in weight over time

### System Requirements

- **Python 3.8+** (automatically detected)- `GET /docs` - Interactive API documentation- `seasonal_patterns`: Higher weight for similar day/week patterns

- **MySQL 8.0+** database server

- **4GB+ RAM** (recommended for large datasets)- `POST /mine` - Start association rule mining- `recency_frequency`: RFM-style weighting combining recency and frequency

- **Windows/Linux/macOS** support

- `GET /status/{task_id}` - Check mining progress- `trend_adaptive`: Adaptive weighting based on purchase trends

### Python Dependencies

See `requirements.txt` for complete list:- `GET /results/{task_id}` - Retrieve mining results

- FastAPI + Uvicorn (API backend)

- Flask (Web interface)**Time Segmentation Options:**

- PyMySQL (Database connectivity)

- Pandas + NumPy (Data processing)### Web Interface (Port 5000)- `weekly`: Analyze patterns by week (default)

- MLxtend (Association rule mining)

- `/` - Main dashboard and database configuration- `monthly`: Analyze patterns by month

## 🐛 Troubleshooting

- `/start-mining` - Begin association rule mining- `daily`: Analyze patterns by day

### Common Issues

- `/view-results` - View and analyze results

**Database Connection Errors:**

- Verify MySQL server is running### 2. Get Recommendations

- Check database credentials in the web interface

- Ensure required tables exist with proper structure## 🛠️ Development



**Import Errors (PyMySQL not found):****GET** `/api/v1/recommendations/{item_name}?limit=10`

- **SOLUTION**: Always use the virtual environment Python

- Use `.venv\Scripts\python.exe` instead of `python`### Setting Up Development Environment

- Batch files automatically detect and use virtual environment

- Main entry point (`main.py`) automatically uses virtual environment```bash### 3. Health Check



**Port Conflicts:**# Clone and enter directory

- Web interface uses port 5000

- FastAPI backend uses port 8001/8080cd association_mining_system**GET** `/api/v1/health`

- Ensure ports are available or modify configuration



### Performance Optimization

- **Large Datasets**: Adjust chunk size in mining configuration# Create virtual environment## Usage Examples

- **Memory Usage**: Monitor RAM usage for large itemset generation

- **Database Performance**: Ensure proper indexing on order tablespython -m venv .venv



### Virtual Environment Issues### Start Enhanced Mining

- **Problem**: `ModuleNotFoundError: No module named 'pymysql'`

- **Solution**: Use virtual environment Python: `.venv\Scripts\python.exe`# Activate virtual environment

- **Batch Files**: Automatically detect and use `.venv` if available

- **Manual Commands**: Always prefix with `.venv\Scripts\python.exe`.venv\Scripts\activate  # Windows```bash



## 🤝 Contributingsource .venv/bin/activate  # Linux/Maccurl -X POST "http://localhost:8000/api/v1/mine-rules" \



1. Fork the repository     -H "Content-Type: application/json" \

2. Create feature branch: `git checkout -b feature/new-feature`

3. Follow existing code structure and naming conventions# Install dependencies     -d '{

4. Add tests for new functionality

5. Update documentationpip install -r requirements.txt       "days_back": 30,

6. Submit pull request

```       "use_enhanced_mining": true,

## 📄 License

       "time_weighting_method": "seasonal_patterns",

This project is licensed under the MIT License - see the LICENSE file for details.

### Project Architecture       "time_segmentation": "weekly"

## 🆘 Support

     }'

For support and questions:

- Check the troubleshooting section above#### Modular Design```

- Review the `/docs` API documentation

- Create an issue in the repository- **app/shared/**: Common components used across features



## ✅ Recent Fixes- **app/modules/**: Individual feature modules with their own API, services, and models### Start Basic Mining



### PyMySQL Import Error Resolution- **app/web/**: Web interface for user interaction

- **Issue**: `ModuleNotFoundError: No module named 'pymysql'` when starting Flask UI

- **Root Cause**: Batch files were using system Python instead of virtual environment- **utils/**: Development and testing utilities```bash

- **Solution**: 

  - Updated all batch files to detect and use `.venv` automaticallycurl -X POST "http://localhost:8000/api/v1/mine-rules" \

  - Modified main entry point to prefer virtual environment Python

  - Added clear instructions for manual startup using virtual environment#### Key Components     -H "Content-Type: application/json" \

- **Status**: ✅ **RESOLVED** - All startup methods now work correctly

- **Configuration Management**: Centralized config handling in `app/shared/config/`     -d '{

### Virtual Environment Auto-Detection

- **Feature**: All startup scripts now automatically detect virtual environment- **Database Layer**: Reusable connection management in `app/shared/database/`       "days_back": 30,

- **Batch Files**: `scripts/*.bat` files use `.venv\Scripts\python.exe` when available

- **Main Entry**: `main.py` prefers virtual environment Python automatically- **Task Management**: Background task tracking in `app/shared/utils/`       "use_enhanced_mining": false

- **Fallback**: System Python used only when no virtual environment exists

- **Service Layer**: Business logic encapsulation in feature-specific services     }'

---

```

**Happy Mining! 🔍✨**
### Adding New Features

1. Create new module in `app/modules/`### Get Recommendations

2. Implement API endpoints, services, and models

3. Add module routes to main FastAPI application```bash

4. Update documentation and testscurl "http://localhost:8000/api/v1/recommendations/MAGGI%202-Minute%20Instant%20Noodles"

```

## 🧪 Testing

## Configuration Parameters

### Run Tests

```bash### Database Configuration

# Run all tests- **DB_HOST**: Database host (default: localhost)

python -m pytest utils/testing/- **DB_USER**: Database username (default: root)

- **DB_PASSWORD**: Database password (default: root)

# Run specific test- **DB_NAME**: Database name (default: neo)

python utils/testing/test_fastapi_config.py- **ORDER_TABLE**: Source table for order data (default: wms_to_wcs_order_line_request_data)

```- **SKU_MASTER_TABLE**: Source table for SKU master data (default: sku_master)

- **RECOMMENDATIONS_TABLE**: Output table for recommendations (default: sku_recommendations)

### Database Utilities

```bash### Mining Parameters

# Check database connection- **MIN_SUPPORT**: Minimum support threshold for frequent itemsets (default: 0.05)

python utils/database/check_table.py- **MIN_CONFIDENCE**: Minimum confidence threshold for rules (default: 0.3)

- **MIN_LIFT**: Minimum lift threshold for rules (default: 1.0)

# Diagnose data quality- **MAX_RECOMMENDATIONS**: Maximum recommendations per item (default: 10)

python utils/database/diagnose_data.py- **DECAY_RATE**: Time decay rate for weighting recent transactions (default: 0.05)



# Test table joins### Enhanced Time-Based Modeling

python utils/database/check_join.py- **DEFAULT_TIME_WEIGHTING_METHOD**: Default time weighting method (default: exponential_decay)

```- **DEFAULT_TIME_SEGMENTATION**: Default time segmentation (default: weekly)

- **USE_ENHANCED_MINING**: Enable enhanced mining by default (default: true)

## 📋 Requirements

### Temporal Scoring Weights (for temporal_weighted scoring method)

### System Requirements- **TEMPORAL_CONFIDENCE_WEIGHT**: Weight for confidence score (default: 0.25)

- **Python 3.8+** (automatically detected)- **TEMPORAL_LIFT_WEIGHT**: Weight for lift score (default: 0.25)

- **MySQL 8.0+** database server- **TEMPORAL_SUPPORT_WEIGHT**: Weight for support score (default: 0.15)

- **4GB+ RAM** (recommended for large datasets)- **TEMPORAL_STABILITY_WEIGHT**: Weight for temporal stability (default: 0.20)

- **Windows/Linux/macOS** support- **TEMPORAL_TREND_WEIGHT**: Weight for temporal trend (default: 0.15)



### Python Dependencies## Database Schema

See `requirements.txt` for complete list:

- FastAPI + Uvicorn (API backend)The system automatically creates the following enhanced table:

- Flask (Web interface)

- PyMySQL (Database connectivity)```sql

- Pandas + NumPy (Data processing)CREATE TABLE sku_recommendations (

- MLxtend (Association rule mining)    id INT AUTO_INCREMENT PRIMARY KEY,

    main_item VARCHAR(512),

## 🐛 Troubleshooting    recommended_item VARCHAR(512),

    confidence_score FLOAT,

### Common Issues    lift_score FLOAT,

    support_score FLOAT,

**Database Connection Errors:**    composite_score FLOAT,

- Verify MySQL server is running    temporal_stability FLOAT DEFAULT NULL,

- Check database credentials in the web interface    temporal_trend FLOAT DEFAULT NULL,

- Ensure required tables exist with proper structure    temporal_composite_score FLOAT DEFAULT NULL,

    recommendation_rank INT,

**Import Errors:**    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

- Activate virtual environment: `.venv\Scripts\activate`    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

- Install dependencies: `pip install -r requirements.txt`    INDEX idx_main_item (main_item),

- Check Python path configuration    INDEX idx_rank (recommendation_rank),

    INDEX idx_temporal_score (temporal_composite_score)

**Port Conflicts:**);

- Web interface uses port 5000```

- FastAPI backend uses port 8001

- Ensure ports are available or modify configuration**New Temporal Fields:**

- `temporal_stability`: Measure of how consistent the rule is across time periods (0-1)

### Performance Optimization- `temporal_trend`: Trend direction of the rule strength (-1 to 1, where 1 = strong positive trend)

- **Large Datasets**: Adjust chunk size in mining configuration- `temporal_composite_score`: Enhanced score incorporating temporal factors

- **Memory Usage**: Monitor RAM usage for large itemset generation

- **Database Performance**: Ensure proper indexing on order tables## Logging



## 🤝 ContributingThe system uses Python's logging module with INFO level by default. Logs include:

- Database connection status

1. Fork the repository- Mining pipeline progress

2. Create feature branch: `git checkout -b feature/new-feature`- API request/response information

3. Follow existing code structure and naming conventions- Error details

4. Add tests for new functionality

5. Update documentation## Production Deployment

6. Submit pull request

For production deployment:

## 📄 License

1. Set `DEBUG=False` in environment

This project is licensed under the MIT License - see the LICENSE file for details.2. Use a production WSGI server (e.g., Gunicorn)

3. Configure reverse proxy (e.g., Nginx)

## 🆘 Support4. Set up monitoring and alerting

5. Use environment-specific database credentials

For support and questions:

- Check the troubleshooting section above## Troubleshooting

- Review the `/docs` API documentation

- Create an issue in the repository### Common Issues



---1. **Import errors**: Make sure all dependencies are installed via `pip install -r requirements.txt`

2. **Database connection errors**: Verify database credentials in `.env` file

**Happy Mining! 🔍✨**3. **No recommendations generated**: Check if there's enough data and adjust MIN_SUPPORT parameter

### Performance Tuning

- Adjust `MIN_SUPPORT` based on your data size
- Use `days_back` parameter to limit historical data
- Monitor database query performance
- Consider adding database indexes for large datasets#   A s s o c i a t i o n _ m i n i n g _ s y s t e m 
 
 