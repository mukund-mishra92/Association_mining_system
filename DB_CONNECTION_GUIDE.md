# Database Connection Guide

## Setup Overview

**Your Setup:**
- **Your Computer:** Where this application runs
- **Remote MySQL Server:** 10.102.246.9 or 10.102.246.10
- **MySQL Configuration:** Binds to `localhost` (not accessible externally)
- **MySQL Port:** 6033
- **Database:** neo
- **Password:** Configured in UI

## Solution: SSH Tunnel (REQUIRED)

Since the MySQL server only accepts connections from `localhost`, you MUST use an SSH tunnel to access it from your computer.

### Quick Start

1. **Start the application with SSH tunnel:**
   ```cmd
   .\start_with_tunnel.bat
   ```

2. **Enter when prompted:**
   - Remote server IP: `10.102.246.9` or `10.102.246.10`
   - SSH username: Your username on the remote server
   - SSH password: Your password for the remote server

3. **Keep the SSH tunnel window open!**

4. **Access the application:**
   - Open browser: http://localhost:5500
   - Enter database password in the UI

### How It Works

```
Your Computer                SSH Tunnel              Remote Server
┌─────────────┐             ┌──────────┐             ┌─────────────┐
│ Application │ ────────────> localhost │ ────────────> MySQL       │
│ localhost:  │   Secure    │ :6033    │   Local     │ localhost:  │
│ 6033        │   Encrypted │          │   Connection│ 6033        │
└─────────────┘             └──────────┘             └─────────────┘
```

The SSH tunnel:
1. Creates a secure encrypted connection to the remote server
2. Forwards local port 6033 to the remote server's localhost:6033
3. Allows your application to connect to "localhost:6033" which is actually the remote MySQL

### Manual Setup (Alternative)

**Step 1: Start SSH Tunnel (in a separate terminal)**
```cmd
.\start_ssh_tunnel.bat
```

**Step 2: Start Application (in another terminal)**
```cmd
.\start.bat
```

### Testing Connection

After starting the SSH tunnel, test it:
```cmd
.\test_connection.bat
```

### Configuration

Your `.env` file should have:
```env
DB_HOST=localhost
DB_PORT=6033
DB_USER=root
DB_PASSWORD=Falcon@WCS@123
DB_NAME=neo
```

**Note:** When using SSH tunnel, always use `DB_HOST=localhost`!
