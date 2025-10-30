# Association Mining System

## Production Deployment Guide

### Prerequisites
- Python 3.8+
- MySQL 8.0+
- 8GB+ RAM recommended
- Network access to MySQL database

### Quick Start

1. **Environment Setup**
   ```bash
   # Copy production environment
   cp .env.production .env
   
   # Edit database credentials
   nano .env
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Database Setup**
   - Ensure MySQL server is running
   - Create database `neo` if not exists
   - Verify source tables exist:
     - `wms_to_wcs_order_line_request_data`
     - `sku_master`

4. **Start Services**
   ```bash
   # Terminal 1: Start API Server
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
   
   # Terminal 2: Start UI Server
   python flask_ui_enhanced.py
   ```

5. **Access Application**
   - UI: http://localhost:5000
   - API: http://localhost:8001

### Production Configuration

#### Database Configuration
- Configure database connection in UI
- Set custom table names if needed
- Test connection before mining

#### Mining Parameters
- **days_back**: Days of historical data (default: 60)
- **top_skus**: Number of top SKUs to analyze (default: 20)
- **min_support**: Minimum support threshold (default: 0.45)
- **min_confidence**: Minimum confidence threshold (default: 0.4)

#### Performance Tuning
- Adjust `MAX_WORKERS` in .env for concurrent processing
- Monitor memory usage during mining
- Use database indexing on ORDER_ID, ARTICLE_ID columns

### API Endpoints

#### Mining
- `POST /mine-rules` - Start association mining
- `GET /task-status/{task_id}` - Check mining progress

#### Configuration
- `POST /api/db-config` - Update database configuration
- `GET /api/db-config` - Get current configuration
- `POST /api/test-db-connection` - Test database connection

#### Mining Options
- `POST /api/mine-direct` - Direct mining (Flask)
- `POST /api/mine-enhanced` - Enhanced temporal mining (FastAPI)

### Monitoring

#### Logs
- Application logs: `association_mining.log`
- Check logs for errors and performance metrics

#### Health Checks
- UI Health: `GET http://localhost:5000/api/test-connection`
- API Health: `GET http://localhost:8001/health`

### Troubleshooting

#### Common Issues
1. **Database Connection Failed**
   - Check MySQL service status
   - Verify credentials in .env
   - Test network connectivity

2. **Mining Takes Too Long**
   - Reduce `days_back` parameter
   - Increase `min_support` threshold
   - Check database performance

3. **Memory Issues**
   - Monitor RAM usage
   - Reduce `top_skus` parameter
   - Optimize database queries

#### Support
- Check application logs
- Verify database table structures
- Monitor system resources

### Security Notes
- Change default SECRET_KEY in production
- Use secure database credentials
- Restrict network access to required ports only
- Regular security updates recommended