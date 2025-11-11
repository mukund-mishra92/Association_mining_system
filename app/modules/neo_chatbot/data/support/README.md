# Support Issues Knowledge Base

Create your support issues document in either JSON or CSV format.

## Template - JSON Format (issues.json)

```json
{
  "issues": [
    {
      "issue_id": "DB_001",
      "issue_name": "Database Connection Failure",
      "category": "database",
      "severity": "critical",
      "symptoms": "Connection error message | Red 'Failed' badge | Pages return 500 errors",
      "root_causes": "MySQL service not running | Incorrect credentials | Firewall blocking port",
      "diagnostic_steps": "Step 1: Check if MySQL service is running | Step 2: Verify credentials | Step 3: Test port 3306",
      "solution_1_title": "Start MySQL Service",
      "solution_1_steps": "Win+R -> Type 'services.msc' -> Find MySQL -> Right-click -> Start",
      "solution_1_type": "client_side",
      "solution_2_title": "Update Database Credentials",
      "solution_2_steps": "Dashboard -> Database Configuration -> Enter correct host/port/user/password -> Save -> Test",
      "solution_2_type": "configuration",
      "prevention": "Set MySQL to auto-start | Enable connection pooling | Configure health monitoring"
    },
    {
      "issue_id": "SCH_001",
      "issue_name": "Mining Scheduler Not Running",
      "category": "scheduler",
      "severity": "high",
      "symptoms": "Scheduler status shows 'Unknown' | Jobs don't execute | No recent job logs",
      "root_causes": "Scheduler not started | FastAPI not running | Schedule inactive",
      "diagnostic_steps": "Step 1: Check scheduler status button | Step 2: Verify FastAPI at localhost:8080/docs | Step 3: Check active schedules list",
      "solution_1_title": "Start Mining Scheduler",
      "solution_1_steps": "Open Association Mining page -> Scroll to Scheduler section -> Click 'Start Scheduler' button",
      "solution_1_type": "client_side",
      "solution_2_title": "Restart FastAPI Backend",
      "solution_2_steps": "Open terminal -> Navigate to NEO folder -> Ctrl+C to stop -> Run: python -m uvicorn app.main:app --port 8080",
      "solution_2_type": "server_side",
      "prevention": "Set up auto-restart | Process monitoring | Health checks"
    }
  ]
}
```

## Template - CSV Format (issues.csv)

```csv
issue_id,issue_name,category,severity,symptoms,root_causes,diagnostic_steps,solution_1_title,solution_1_steps,solution_1_type,solution_2_title,solution_2_steps,solution_2_type,prevention
DB_001,Database Connection Failure,database,critical,"Connection error | Red badge | 500 errors","MySQL stopped | Wrong credentials | Port blocked","Check MySQL service | Verify credentials | Test port 3306",Start MySQL Service,"Win+R -> services.msc -> Start MySQL",client_side,Update Credentials,"Dashboard -> Config -> Update -> Test",configuration,"Auto-start | Health monitoring"
SCH_001,Scheduler Not Running,scheduler,high,"Status Unknown | No jobs | No logs","Not started | FastAPI down | Inactive","Check status | Verify FastAPI | Check schedules",Start Scheduler,"Mining page -> Start Scheduler button",client_side,Restart FastAPI,"Terminal -> Ctrl+C -> python -m uvicorn app.main:app",server_side,"Auto-restart | Monitoring"
```

## Field Descriptions

| Field | Description | Example |
|-------|-------------|---------|
| `issue_id` | Unique identifier | DB_001, SCH_001 |
| `issue_name` | Clear issue name | "Database Connection Failure" |
| `category` | Issue category | database, scheduler, mining, performance, api, ui |
| `severity` | How critical | critical, high, medium, low |
| `symptoms` | What user sees (pipe-separated) | "Error message \| Red badge \| 500 errors" |
| `root_causes` | Possible causes (pipe-separated) | "Service stopped \| Wrong config \| Port blocked" |
| `diagnostic_steps` | Troubleshooting steps (pipe-separated) | "Step 1: Check X \| Step 2: Verify Y" |
| `solution_1_title` | First solution name | "Start MySQL Service" |
| `solution_1_steps` | Step-by-step instructions | "Win+R -> services.msc -> Start" |
| `solution_1_type` | Solution type | client_side, server_side, configuration |
| `solution_2_title` | Alternative solution | "Update Credentials" |
| `solution_2_steps` | Alternative steps | "Dashboard -> Config -> Save" |
| `solution_2_type` | Alternative type | client_side, server_side, configuration |
| `prevention` | How to prevent (pipe-separated) | "Auto-start \| Monitoring \| Health checks" |

## Categories

- `database` - Database connection, query, performance issues
- `scheduler` - Mining scheduler, job execution issues
- `mining` - Association mining algorithm, results issues
- `performance` - Slow loading, timeouts, resource issues
- `api` - API errors, endpoint failures
- `ui` - Interface problems, display issues

## Severity Levels

- `critical` - System unusable, immediate fix needed
- `high` - Major feature broken, work blocked
- `medium` - Feature degraded, workaround exists
- `low` - Minor issue, cosmetic problem

## Solution Types

- `client_side` - User can fix without server access (restart service, clear cache, etc.)
- `server_side` - Requires server/terminal access (restart services, run commands)
- `configuration` - Change settings/config files

## Example Use

When a user says "My database is not connecting", the chatbot will:
1. Search for matching issues (finds DB_001)
2. Confirm symptoms with user
3. Guide through diagnostic steps
4. Provide appropriate solution
5. Suggest prevention tips

---

## Getting Started

1. Choose JSON or CSV format (JSON recommended for complex data)
2. List all common issues you've encountered
3. Add symptoms, causes, and solutions
4. Save as `issues.json` or `issues.csv` in this folder
5. Chatbot will automatically load and use it!

**Tip**: Start with 5-10 most common issues, you can add more later.
