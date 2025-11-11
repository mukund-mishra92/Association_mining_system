# Association Mining System

Warehouse intelligence platform for order pattern analysis and inventory optimization.

## What it does

This system helps you analyze your warehouse order data to:
- Find patterns in customer orders
- Get AI-powered inventory recommendations  
- See demand forecasts and trends
- Optimize SKU performance

## Requirements

- Python 3.8 or newer
- MySQL 8.0 or newer
- At least 4GB RAM

## Installation

1. Download or clone the project
2. Open command prompt and go to the project folder:
   ```
   cd association_mining_system
   ```

3. Create a virtual environment:
   ```
   python -m venv .venv
   ```

4. Activate the virtual environment:
   ```
   .venv\Scripts\activate
   ```

5. Install required packages:
   ```
   pip install -r requirements.txt
   ```

## How to run

### Easy way (recommended)
```
python main.py
```

### Using batch files (Windows only)
```
quick_start.bat
```

## How to use

1. Start the system using one of the methods above
2. Open your web browser
3. Go to: http://localhost:5000
4. Set up your database connection
5. Upload your order data
6. Run the analysis
7. View results in the dashboard

## Web Interface

The main dashboard runs at: http://localhost:5000

Features:
- Database setup
- Data upload and validation
- Start analysis
- View results and charts
- Download reports

## API Interface

The API runs at: http://localhost:8001

Key endpoints:
- `/docs` - See all available API functions
- `/mine` - Start data analysis
- `/recommendations/{item}` - Get recommendations for an item
- `/health` - Check if system is working

## Database Setup

You need these tables in your MySQL database:
- Order data table (your transaction records)
- SKU master table (product information)

The system will create a recommendations table automatically.

## Configuration

Create a `.env` file with your settings:
```
DB_HOST=localhost
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=your_database
ORDER_TABLE=your_order_table_name
SKU_MASTER_TABLE=your_sku_table_name
```

## Troubleshooting

**Cannot start the system:**
- Make sure Python is installed
- Check that MySQL is running
- Activate the virtual environment first

**Database connection errors:**
- Verify your database credentials
- Make sure MySQL service is running
- Check if tables exist

**Module not found errors:**
- Activate virtual environment: `.venv\Scripts\activate`
- Install packages: `pip install -r requirements.txt`

**Port conflicts:**
- Web interface uses port 5000
- API uses port 8001
- Make sure these ports are available

## Getting Help

If you need help:
1. Check the troubleshooting section above
2. Look at the API documentation at http://localhost:8001/docs
3. Check the log files for error messages

## Files and Folders

```
association_mining_system/
├── main.py                 # Start the system
├── requirements.txt        # Required packages
├── scripts/               # Batch files for Windows
├── app/                   # Main application code
│   ├── main.py           # API backend
│   ├── web/              # Web dashboard
│   ├── modules/          # Analysis features
│   └── shared/           # Common code
└── utils/                # Helper tools
```

That's it! The system should work for analyzing your warehouse data and providing insights.