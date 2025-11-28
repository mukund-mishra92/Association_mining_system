# Association Mining System 🔗

A comprehensive data mining platform for analyzing customer purchase patterns and SKU performance. Built with Flask, FastAPI, and MySQL.

## ✨ New Features

� **Windows Service Support** - Run the system as a background Windows service with auto-restart capabilities  
🔑 **Primary Keys on All Tables** - Enhanced database integrity with proper primary keys on all tables  
📊 **Scheduler Service** - Automated mining jobs with configurable schedules  
🔄 **Auto-Recovery** - Automatic process restart on failures  

**📖 See [SERVICE_SETUP.md](SERVICE_SETUP.md) for complete setup instructions**
# Association Mining System — Quick Commands

Minimal, one-liners to set up and run on Windows PowerShell.

## Setup (first time)
- Create venv: `python -m venv .venv`
- Activate venv: `.\\.venv\\Scripts\\Activate.ps1`
- Install deps: `pip install --upgrade pip; pip install -r requirements.txt`
- Create env (if missing): `Copy-Item .env.example .env` (then edit DB settings)

## Run (development)
- Start both servers (bg): `.\\quick_start.bat` — FastAPI:8080 + Flask:5000
- Stop both servers: `.\\stop_servers.bat`
- Start via Python: `python .\\run_servers.py start` — Starts both
- Stop via Python: `python .\\run_servers.py stop` — Stops both

## Windows Service (Admin)
- Install service: `.\\scripts\\service\\install_service.bat` — Registers Windows service
- Start service: `.\\scripts\\service\\start_service.bat` — Runs in background
- Stop service: `.\\scripts\\service\\stop_service.bat` — Stops the service
- Check status: `.\\scripts\\service\\check_service.bat` — Shows status
- Uninstall: `.\\scripts\\service\\uninstall_service.bat` — Removes service

## URLs
- UI: http://localhost:5000
- API: http://localhost:8080
- Docs: http://localhost:8080/docs

## Logs
- Folder: `logs\\` — Service and server logs

- **Status**: ✅ **RESOLVED** - All startup methods now work correctly

- **Configuration Management**: Centralized config handling in `app/shared/config/`     -d '{


- **Feature**: All startup scripts now automatically detect virtual environment- **Database Layer**: Reusable connection management in `app/shared/database/`       "days_back": 30,

- **Batch Files**: `scripts/*.bat` files use `.venv\Scripts\python.exe` when available

- **Main Entry**: `main.py` prefers virtual environment Python automatically- **Task Management**: Background task tracking in `app/shared/utils/`       "use_enhanced_mining": false


- **Service Layer**: Business logic encapsulation in feature-specific services     }'

---

```

1. Create new module in `app/modules/`### Get Recommendations





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