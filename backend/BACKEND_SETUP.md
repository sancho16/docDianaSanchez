# Backend API Setup Guide

This guide walks you through setting up the Flask backend API on your server at `192.168.0.131`.

## Prerequisites

- SSH access to `beckham23@192.168.0.131`
- MySQL database running
- Python 3.8+ installed
- `pip3` installed

## Step 1: Prepare the Server

SSH into your server:

```bash
ssh beckham23@192.168.0.131
```

Install required packages:

```bash
# Update system
sudo apt update

# Install Python pip if not installed
sudo apt install python3-pip python3-venv -y

# Install MySQL client libraries
sudo apt install libmysqlclient-dev python3-dev -y
```

## Step 2: Upload Backend Files

From your local machine, upload the backend directory:

```bash
cd /Users/juliansanchez/docDianaSanchez

# Upload entire backend folder
scp -r backend/* beckham23@192.168.0.131:~/diana-booking-backend/
```

## Step 3: Configure Database

On the server, create the database:

```bash
ssh beckham23@192.168.0.131

# Connect to MySQL
mysql -u beckham23 -p

# Create production database
CREATE DATABASE IF NOT EXISTS diana_bookings 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

# Create staging database (optional but recommended)
CREATE DATABASE IF NOT EXISTS diana_bookings_staging 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

# Verify databases
SHOW DATABASES;

EXIT;
```

## Step 4: Configure Environment

Create the `.env` file:

```bash
cd ~/diana-booking-backend

# Copy example to .env
cp .env.example .env

# Edit with your actual credentials
nano .env
```

Update the `.env` file with your actual database password:

```env
# Database Configuration
DATABASE_HOST=localhost
DATABASE_USER=beckham23
DATABASE_PASSWORD=YOUR_ACTUAL_PASSWORD_HERE
DATABASE_NAME=diana_bookings
DATABASE_PORT=3306

# Server Configuration
PORT=8000
ENVIRONMENT=production
```

**Important**: Replace `YOUR_ACTUAL_PASSWORD_HERE` with your actual MySQL password!

## Step 5: Install Python Dependencies

```bash
cd ~/diana-booking-backend

# Install required packages
pip3 install -r requirements.txt
```

If you encounter issues, try:

```bash
pip3 install --upgrade pip
pip3 install -r requirements.txt --user
```

## Step 6: Test the Setup

Test database connection:

```bash
cd ~/diana-booking-backend

python3 -c "
from dotenv import load_dotenv
import mysql.connector
import os

load_dotenv()

try:
    conn = mysql.connector.connect(
        host=os.getenv('DATABASE_HOST'),
        user=os.getenv('DATABASE_USER'),
        password=os.getenv('DATABASE_PASSWORD'),
        database=os.getenv('DATABASE_NAME')
    )
    print('✅ Database connection successful!')
    print(f'Connected to: {os.getenv(\"DATABASE_NAME\")}')
    conn.close()
except Exception as e:
    print(f'❌ Connection failed: {e}')
"
```

Test the Flask app manually:

```bash
cd ~/diana-booking-backend
python3 app.py
```

You should see:
```
* Running on http://0.0.0.0:8000
Database tables initialized successfully
```

Press `Ctrl+C` to stop it, then start it properly in the background.

## Step 7: Start the Backend Server

Using the deployment script:

```bash
cd ~/diana-booking-backend

# Make deploy script executable
chmod +x deploy.sh

# Deploy to production
./deploy.sh production
```

Or manually:

```bash
cd ~/diana-booking-backend

# Start in background
nohup python3 app.py > backend.log 2>&1 &

# Get the process ID
echo $!

# Check logs
tail -f backend.log
```

## Step 8: Verify API is Running

Test from the server:

```bash
# Health check
curl http://localhost:8000/api/health

# Should return something like:
# {"status":"ok","service":"Dr. Diana Sánchez Booking API","database":"connected","timestamp":"2026-07-23T..."}
```

Test from your local machine:

```bash
curl http://192.168.0.131:8000/api/health
```

## Step 9: Configure Nginx (Optional but Recommended)

If you want to expose the API via a domain name:

```bash
sudo nano /etc/nginx/sites-available/api-diana
```

Add:

```nginx
server {
    listen 80;
    server_name api.docdianasanchez.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and restart:

```bash
sudo ln -s /etc/nginx/sites-available/api-diana /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Step 10: Test the Full Flow

From your browser:

1. Open: `https://docdianasanchez.com`
2. Fill out the booking form
3. Submit the form
4. Check the admin panel: `https://docdianasanchez.com/admin/`
5. Login with password: `diana2024`
6. You should see the appointment with device tracking info!

## Troubleshooting

### Problem: Database connection failed

**Solution:**
```bash
# Check MySQL is running
sudo systemctl status mysql

# Test connection manually
mysql -u beckham23 -p diana_bookings -e "SELECT 1;"

# Verify .env file has correct credentials
cat ~/diana-booking-backend/.env
```

### Problem: Port already in use

**Solution:**
```bash
# Find what's using port 8000
sudo lsof -i :8000

# Kill the process
sudo kill -9 <PID>

# Or use different port in .env
nano ~/diana-booking-backend/.env
# Change PORT=8000 to PORT=8001
```

### Problem: Module not found (Flask, mysql-connector, etc.)

**Solution:**
```bash
# Reinstall dependencies
cd ~/diana-booking-backend
pip3 install -r requirements.txt --force-reinstall
```

### Problem: API returns 500 error

**Solution:**
```bash
# Check logs
tail -50 ~/diana-booking-backend/backend.log

# Check if database tables exist
mysql -u beckham23 -p diana_bookings -e "SHOW TABLES;"
```

### Problem: Admin panel shows no data

**Possible causes:**

1. **API not running**: Check if backend is running
   ```bash
   ps aux | grep python3
   curl http://localhost:8000/api/health
   ```

2. **CORS issues**: Check browser console for errors
   - Backend has CORS enabled, so this should work

3. **Wrong API URL**: Verify in admin.js
   ```javascript
   const API_URL = 'https://api.docdianasanchez.com';
   ```

4. **Fallback to localStorage**: Admin panel falls back to localStorage if API fails
   - Check browser console for error messages

## Maintenance

### View logs

```bash
tail -f ~/diana-booking-backend/backend.log
```

### Stop the server

```bash
pkill -f "python3 app.py"
```

### Restart the server

```bash
cd ~/diana-booking-backend
./deploy.sh production
```

### Update the code

```bash
cd ~/diana-booking-backend
git pull origin main
./deploy.sh production
```

### Backup database

```bash
mysqldump -u beckham23 -p diana_bookings > backup_$(date +%Y%m%d).sql
```

### Restore database

```bash
mysql -u beckham23 -p diana_bookings < backup_20260723.sql
```

## Security Notes

1. **Never commit .env file** - It contains sensitive credentials
2. **Use strong database password** - Change from default
3. **Enable firewall** - Only allow necessary ports
4. **Use HTTPS** - Install SSL certificate for API domain
5. **Regular backups** - Backup database daily
6. **Update dependencies** - Keep Python packages updated

## API Endpoints

Once running, these endpoints are available:

- `GET /api/health` - Health check
- `POST /api/bookings` - Create new booking
- `GET /api/bookings` - Get all bookings
- `GET /api/bookings?status=pending` - Filter by status
- `PATCH /api/bookings/{id}` - Update booking status
- `DELETE /api/bookings/{id}` - Delete booking
- `POST /api/reviews` - Create new review
- `GET /api/reviews` - Get approved reviews
- `GET /api/reviews?approved=false` - Get all reviews
- `PATCH /api/reviews/{id}/approve` - Approve review
- `DELETE /api/reviews/{id}` - Delete review

## Support

If you encounter issues:

1. Check logs: `tail -f ~/diana-booking-backend/backend.log`
2. Test database: `mysql -u beckham23 -p diana_bookings -e "SHOW TABLES;"`
3. Test API: `curl http://localhost:8000/api/health`
4. Check process: `ps aux | grep python3`

Good luck! 🚀
