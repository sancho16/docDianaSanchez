# 📦 Server Files Inventory
**Dr. Diana Sánchez Booking System**

## Server Information

**Server**: `beckham23@192.168.0.131`  
**Backend Directory**: `/home/beckham23/diana-booking-backend/`  
**Backend Port**: `8000` (internal)  
**Public URL**: `https://api.docdianasanchez.com`  
**Database**: PostgreSQL - `diana_bookings`

---

## 🗂️ Current Files on Server

### Backend Directory Structure
```
/home/beckham23/diana-booking-backend/
│
├── 📄 app.py                          ← Main Flask application (LIVE)
├── 📄 app.py.backup-*                 ← Multiple timestamped backups
├── 📄 app_full_backup.py              ← Full application backup
├── 📄 app_postgres.py                 ← PostgreSQL version backup
├── 📄 app_updated.py                  ← Updated version backup
│
├── 📄 notify.py                       ← ⚠️ MISSING - Email notification module (needs upload)
│
├── 📁 .env                            ← Environment configuration (DATABASE, SMTP)
├── 📄 .env.example                    ← Environment template
│
├── 📄 requirements.txt                ← Python dependencies
│   ├─ Flask==3.0.0
│   ├─ Flask-CORS==4.0.0
│   ├─ psycopg2-binary==2.9.9         ← PostgreSQL driver
│   ├─ python-dotenv==1.0.0
│   └─ google-auth==2.25.2             ← For Google Sign-In
│
├── 📁 venv/ or faker-env/             ← Python virtual environment
│
├── 📄 gunicorn.log                    ← Web server logs
├── 📄 restart_backend.sh              ← Backend restart script
├── 📄 reload_server.sh                ← Server reload script
├── 📄 verify_changes.sh               ← Changes verification script
├── 📄 deploy.sh                       ← Deployment script
├── 📄 deploy_updated.sh               ← Updated deployment script
├── 📄 deploy_updated_fixed.sh         ← Fixed deployment script
│
├── 📄 update_admin_theme.py           ← Admin theme updater
├── 📄 update_admin_view.py            ← Admin view updater
├── 📄 add_route_manual.py             ← Route addition script
├── 📄 add_medical_records_route.py    ← Medical records route script
│
├── 📄 medical_records_template.html   ← Medical records HTML template
│
├── 📄 URGENT_FIX.sh                   ← Emergency fix script
├── 📄 add_get_bookings.patch          ← Patch file for GET endpoint
├── 📄 admin_view_updates.patch        ← Patch file for admin updates
│
└── 📁 data/                           ← Data directory (if exists)
```

---

## 🚨 Missing Critical File

### ⚠️ notify.py - Email Notification Module
**Status**: **NOT ON SERVER** (needs to be uploaded)

**Location on Local**:
```
/Users/juliansanchez/docDianaSanchez/backend/notify.py
```

**What it does**:
- Sends booking confirmation emails to patients
- Sends appointment notifications to Dr. Diana
- Sends visit completion summaries
- Handles SMTP authentication and email formatting

**Why it's critical**:
- Without it: Bookings save but NO emails are sent
- With it: Complete notification system works

**Upload command**:
```bash
scp /Users/juliansanchez/docDianaSanchez/backend/notify.py \
    beckham23@192.168.0.131:~/diana-booking-backend/
```

---

## 📊 Database (PostgreSQL)

### Database Details
```
Host: localhost (on server)
User: beckham23 or diana_app
Database: diana_bookings
Port: 5432 (default PostgreSQL)
```

### Tables
```sql
-- Main bookings table
bookings (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    patient_id VARCHAR(50),
    phone VARCHAR(20),
    email VARCHAR(255),
    channel VARCHAR(50),           -- virtual, express
    virtual_platform VARCHAR(100),  -- WhatsApp, Zoom, Meet, Phone
    address TEXT,
    address_city VARCHAR(100),
    address_province VARCHAR(100),
    gps_coordinates VARCHAR(255),
    service VARCHAR(255),
    preferred_date DATE,
    preferred_time TIME,
    message TEXT,
    status VARCHAR(50),            -- pending, confirmed, completed, cancelled
    is_dummy BOOLEAN,
    
    -- Device tracking fields
    ip_address VARCHAR(50),
    ip_country VARCHAR(100),
    ip_city VARCHAR(100),
    device_type VARCHAR(50),
    device_brand VARCHAR(100),
    device_model VARCHAR(100),
    device_os VARCHAR(100),
    device_browser VARCHAR(100),
    screen_size VARCHAR(50),
    user_language VARCHAR(10),
    user_timezone VARCHAR(100),
    connection_type VARCHAR(50),
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Medical records tables (if implemented)
visits (...)
medications (...)
symptoms (...)
patient_history (...)
```

### Current Data
- **80 appointments** stored
- Mix of real and test data
- Device tracking information captured

---

## 🔧 Configuration Files

### .env File (on server)
```bash
# Database Configuration
DATABASE_URL=postgresql://diana_app@localhost/diana_bookings

# Server Configuration
PORT=8000
ENVIRONMENT=production
ALLOWED_ORIGINS=https://docdianasanchez.com,https://www.docdianasanchez.com

# Admin Configuration
ADMIN_TOKEN=your_secure_admin_token_here
GOOGLE_CLIENT_ID=your_google_client_id_here
ALLOWED_ADMINS=drasanchezd94@gmail.com

# Email (SMTP) Configuration - ⚠️ NEEDS TO BE ADDED
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=drasanchezd94@gmail.com
SMTP_PASSWORD=your_app_password_here     # ← NEEDS TO BE CONFIGURED
SMTP_FROM_EMAIL=drasanchezd94@gmail.com
SMTP_FROM_NAME=Dr. Diana Sánchez
DOCTOR_EMAIL=drasanchezd94@gmail.com

# WhatsApp Configuration
WHATSAPP_NOTIFICATION=true
DOCTOR_WHATSAPP=+50683493378
```

---

## 🌐 Running Process

### Gunicorn Web Server
```bash
# Process
~/faker-env/bin/gunicorn -w 2 -b 127.0.0.1:8000 --reuse-port app:app

# Check if running
ps aux | grep gunicorn

# Typical output:
beckham23  12345  ... gunicorn: master [app:app]
beckham23  12346  ... gunicorn: worker [app:app]
beckham23  12347  ... gunicorn: worker [app:app]
```

### Nginx Reverse Proxy
```
External Request → Nginx (80/443) → Gunicorn (8000) → Flask app.py
```

**Nginx config likely at**:
- `/etc/nginx/sites-available/diana-api`
- `/etc/nginx/sites-enabled/diana-api`

---

## 🔄 Deployment Workflow

### Local Development
```
/Users/juliansanchez/docDianaSanchez/
├── backend/
│   ├── app.py                  ← Source of truth
│   ├── notify.py               ← NEW (not on server yet)
│   ├── .env.example            ← Template
│   └── requirements.txt        ← Dependencies
```

### Transfer to Server
```bash
# Upload single file
scp backend/notify.py beckham23@192.168.0.131:~/diana-booking-backend/

# Upload entire backend
scp -r backend/* beckham23@192.168.0.131:~/diana-booking-backend/

# SSH and restart
ssh beckham23@192.168.0.131
cd diana-booking-backend
sudo bash restart_backend.sh
```

### GitHub Repository
```
Repository: https://github.com/sancho16/docDianaSanchez
Branch: main
Backend files: /backend/
```

---

## 📋 What Needs to Be Uploaded Now

### Critical Missing Files
1. **notify.py** - Email notification system
   ```bash
   scp backend/notify.py beckham23@192.168.0.131:~/diana-booking-backend/
   ```

2. **Updated .env configuration** - SMTP settings
   - Needs Gmail App Password configured
   - Edit directly on server: `nano ~/diana-booking-backend/.env`

### Optional Supporting Files
3. **test_email.py** - Email testing script
   ```bash
   scp backend/test_email.py beckham23@192.168.0.131:~/diana-booking-backend/
   ```

4. **EMAIL_SETUP_GUIDE.md** - Documentation
   ```bash
   scp backend/EMAIL_SETUP_GUIDE.md beckham23@192.168.0.131:~/diana-booking-backend/
   ```

---

## 🚀 Complete Upload & Restart Procedure

### Step 1: Upload Missing Files
```bash
# From your local machine
cd /Users/juliansanchez/docDianaSanchez

# Upload notify.py (critical)
scp backend/notify.py beckham23@192.168.0.131:~/diana-booking-backend/

# Upload test script (optional but helpful)
scp backend/test_email.py beckham23@192.168.0.131:~/diana-booking-backend/

# Make test script executable
ssh beckham23@192.168.0.131 "chmod +x ~/diana-booking-backend/test_email.py"
```

### Step 2: Configure Email Settings
```bash
# SSH to server
ssh beckham23@192.168.0.131

# Edit .env file
cd ~/diana-booking-backend
nano .env

# Add SMTP configuration (see .env section above)
# Save: Ctrl+X, Y, Enter
```

### Step 3: Test Email Configuration
```bash
# Still on server
cd ~/diana-booking-backend
python3 test_email.py

# Should show:
# ✓ All required variables are set
# ✓ Connected to SMTP server
# ✓ Authentication successful
```

### Step 4: Restart Backend
```bash
# Still on server
sudo bash ~/diana-booking-backend/restart_backend.sh

# Verify it's running
ps aux | grep gunicorn
curl http://localhost:8000/api/health
```

### Step 5: Test End-to-End
```bash
# From your computer, submit a test booking:
# Visit: https://docdianasanchez.com
# Fill form and submit
# Check email: drasanchezd94@gmail.com
```

---

## 📊 Server Monitoring

### Check Backend Status
```bash
# Is it running?
ssh beckham23@192.168.0.131 "ps aux | grep gunicorn"

# View recent logs
ssh beckham23@192.168.0.131 "tail -50 ~/diana-booking-backend/gunicorn.log"

# Monitor live logs
ssh beckham23@192.168.0.131 "tail -f ~/diana-booking-backend/gunicorn.log"

# Check API health
curl https://api.docdianasanchez.com/api/health
```

### Check Database Status
```bash
ssh beckham23@192.168.0.131
psql -U diana_app -d diana_bookings -c "SELECT COUNT(*) FROM bookings;"
```

---

## 🔐 File Permissions

### Important Files Should Have:
```bash
# Application files
-rw-r--r--  app.py
-rw-r--r--  notify.py
-rwxr-xr-x  restart_backend.sh  (executable)
-rwxr-xr-x  test_email.py       (executable)

# Sensitive files
-rw-------  .env                (read-only by owner)
```

### Set Correct Permissions
```bash
ssh beckham23@192.168.0.131
cd ~/diana-booking-backend
chmod 600 .env                    # Secure .env
chmod +x restart_backend.sh       # Make executable
chmod +x test_email.py            # Make executable
```

---

## 🗺️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENT BROWSER                       │
│              https://docdianasanchez.com                │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   GITHUB PAGES                          │
│           Serves: HTML, CSS, JS, Assets                 │
│              (Frontend static files)                    │
└────────────────────────┬────────────────────────────────┘
                         │
                         │ API Calls
                         ▼
┌─────────────────────────────────────────────────────────┐
│              CLOUDFLARE / DNS                           │
│        api.docdianasanchez.com → 192.168.0.131         │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│           SERVER: beckham23@192.168.0.131               │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Nginx (Port 80/443)                  │  │
│  │         Reverse Proxy + SSL/TLS                   │  │
│  └─────────────────────┬────────────────────────────┘  │
│                        │                                │
│                        ▼                                │
│  ┌──────────────────────────────────────────────────┐  │
│  │        Gunicorn (Port 8000 - internal)            │  │
│  │              2 worker processes                    │  │
│  └─────────────────────┬────────────────────────────┘  │
│                        │                                │
│                        ▼                                │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Flask Application                     │  │
│  │          ~/diana-booking-backend/                  │  │
│  │                                                    │  │
│  │  • app.py         (Main application)              │  │
│  │  • notify.py      (Email system) ← MISSING       │  │
│  │  • .env           (Configuration)                 │  │
│  │  • requirements.txt (Dependencies)                │  │
│  └─────────────────────┬────────────────────────────┘  │
│                        │                                │
│                        ▼                                │
│  ┌──────────────────────────────────────────────────┐  │
│  │          PostgreSQL Database                      │  │
│  │           diana_bookings                          │  │
│  │                                                    │  │
│  │  • bookings table (80 appointments)               │  │
│  │  • visits table (medical records)                 │  │
│  │  • medications, symptoms, etc.                    │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
                         │
                         │ SMTP
                         ▼
┌─────────────────────────────────────────────────────────┐
│               Gmail SMTP Server                         │
│           smtp.gmail.com:587 (TLS)                      │
│                                                         │
│  Sends emails:                                          │
│  • Doctor notifications → drasanchezd94@gmail.com       │
│  • Patient confirmations → patient email                │
└─────────────────────────────────────────────────────────┘
```

---

## 📝 Quick Command Reference

```bash
# ======================
# FILE UPLOADS
# ======================

# Upload notify.py
scp backend/notify.py beckham23@192.168.0.131:~/diana-booking-backend/

# Upload multiple files
scp backend/{notify.py,test_email.py} beckham23@192.168.0.131:~/diana-booking-backend/

# ======================
# SERVER ACCESS
# ======================

# SSH to server
ssh beckham23@192.168.0.131

# Navigate to backend
cd ~/diana-booking-backend

# ======================
# SERVICE MANAGEMENT
# ======================

# Restart backend
sudo bash restart_backend.sh

# Check if running
ps aux | grep gunicorn

# Kill and restart manually
sudo pkill -f "gunicorn.*app:app"
cd ~/diana-booking-backend
sudo nohup ~/faker-env/bin/gunicorn -w 2 -b 127.0.0.1:8000 --reuse-port app:app > gunicorn.log 2>&1 &

# ======================
# MONITORING
# ======================

# View logs
tail -50 gunicorn.log

# Follow logs in real-time
tail -f gunicorn.log

# Check API health
curl http://localhost:8000/api/health

# Test bookings endpoint
curl http://localhost:8000/api/bookings | python3 -m json.tool | head -50

# ======================
# DATABASE
# ======================

# Connect to database
psql -U diana_app -d diana_bookings

# Quick queries
psql -U diana_app -d diana_bookings -c "SELECT COUNT(*) FROM bookings;"
psql -U diana_app -d diana_bookings -c "SELECT name, email, created_at FROM bookings ORDER BY created_at DESC LIMIT 5;"

# ======================
# EMAIL TESTING
# ======================

# Test email configuration
python3 test_email.py

# Test notify module directly
python3 notify.py
```

---

## 🎯 Next Actions Required

### Immediate (To Fix Email Issue)
1. ✅ Upload `notify.py` to server
2. ✅ Configure SMTP settings in `.env`
3. ✅ Test email with `test_email.py`
4. ✅ Restart backend
5. ✅ Verify emails are sent

### Commands to Run
```bash
# 1. Upload
scp backend/notify.py beckham23@192.168.0.131:~/diana-booking-backend/

# 2. Configure
ssh beckham23@192.168.0.131
nano ~/diana-booking-backend/.env
# Add SMTP_PASSWORD=your_app_password_here

# 3. Test
python3 ~/diana-booking-backend/test_email.py

# 4. Restart
sudo bash ~/diana-booking-backend/restart_backend.sh

# 5. Test end-to-end
# Visit website and submit booking
```

---

## 📚 Documentation Files (Local)

Reference these for detailed instructions:

```
/Users/juliansanchez/docDianaSanchez/
├── EMAIL_FIX_SUMMARY.md              ← Complete fix overview
├── backend/
│   ├── EMAIL_SETUP_GUIDE.md          ← Step-by-step email setup
│   ├── test_email.py                 ← Email testing tool
│   └── notify.py                     ← Email module (ready to upload)
├── DEPLOYMENT_UPDATE_JUL23_2026.md   ← Latest deployment info
├── CURRENT_STATUS.md                 ← System status
├── BACKEND_RESTART_INSTRUCTIONS.md   ← Restart procedures
└── docs/
    └── DEPLOYMENT_GUIDE.md           ← Full deployment guide
```

---

## ✅ Summary

### What's on Server Now
- ✅ Flask application (app.py)
- ✅ Database with 80 bookings
- ✅ Gunicorn web server running
- ✅ Medical records system
- ✅ Admin panel
- ❌ Email notification module (notify.py) **← MISSING**

### What Needs to Be Added
1. Upload `notify.py` to server
2. Configure Gmail App Password in `.env`
3. Restart backend
4. Test email notifications

### Result
Once completed, the booking system will send:
- Doctor notifications for new bookings
- Patient confirmation emails
- Visit completion summaries

**Estimated time to complete**: 10 minutes

---

*Last Updated: July 23, 2026*
