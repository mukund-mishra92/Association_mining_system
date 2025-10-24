# Database Connection Guide

## Current Issue
The MySQL server on `10.102.246.10` is configured to only accept connections from `localhost`, not from remote IPs.

## Solutions

### Option 1: SSH Tunnel (Recommended)

1. Open a terminal and create an SSH tunnel:
   ```bash
   ssh -L 6033:localhost:6033 your_username@10.102.246.10
   ```
   Leave this terminal open while using the application.

2. Update `.env` file:
   ```env
   DB_HOST=localhost
   DB_PORT=6033
   DB_USER=root
   DB_PASSWORD=Falcon@WCS@123
   DB_NAME=neo
   ```

3. Restart the application

### Option 2: Configure MySQL for Remote Access (Requires Server Admin)

On the server `10.102.246.10`, an administrator needs to:

1. Edit MySQL config file (`my.cnf` or `my.ini`):
   ```ini
   [mysqld]
   bind-address = 0.0.0.0
   port = 6033
   ```

2. Grant remote access to root user:
   ```sql
   CREATE USER 'root'@'%' IDENTIFIED BY 'Falcon@WCS@123';
   GRANT ALL PRIVILEGES ON neo.* TO 'root'@'%';
   FLUSH PRIVILEGES;
   ```

3. Configure firewall to allow port 6033

4. Restart MySQL service

### Option 3: Use a Different User Account

Create a dedicated user for remote access:

```sql
CREATE USER 'remote_user'@'%' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON neo.* TO 'remote_user'@'%';
FLUSH PRIVILEGES;
```

Then update `.env`:
```env
DB_HOST=10.102.246.10
DB_PORT=6033
DB_USER=remote_user
DB_PASSWORD=secure_password
DB_NAME=neo
```

## Testing Connection

Test if MySQL is accessible:
```powershell
Test-NetConnection -ComputerName 10.102.246.10 -Port 6033
```

Test MySQL login:
```bash
mysql -h 10.102.246.10 -P 6033 -u root -p neo
```
