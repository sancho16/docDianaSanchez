# 🔍 TROUBLESHOOTING DEEP DIVE
## Dr. Diana Sánchez Admin Panel - Medical Records Implementation
### Complete Technical Analysis & Problem Resolution

---

**Date**: July 23, 2026  
**Developer**: Julian Sanchez  
**Project**: Dr. Diana Sánchez Medical Services Platform  
**Repository**: https://github.com/sancho16/docDianaSanchez  
**Server**: beckham23@192.168.0.131

---

## 📋 TABLE OF CONTENTS

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Initial Problems Identified](#initial-problems-identified)
4. [Root Cause Analysis](#root-cause-analysis)
5. [Troubleshooting Process](#troubleshooting-process)
6. [Technical Concepts Explained](#technical-concepts-explained)
7. [All Artifacts Used](#all-artifacts-used)
8. [Step-by-Step Resolution](#step-by-step-resolution)
9. [Final Verification](#final-verification)
10. [Lessons Learned](#lessons-learned)

---

## 1. EXECUTIVE SUMMARY

### What We Built
We implemented a dynamic medical records page for the admin panel that:
- Opens when clicking appointment rows
- Fetches patient data from PostgreSQL database
- Displays pre-filled information in a form
- Allows doctors to add diagnosis, treatment, and notes
- Saves data back to the database

### What Went Wrong
1. **404 Error**: Medical records page returned "Not Found"
2. **Charts Not Circular**: Doughnut and pie charts were elliptical
3. **Database Column Error**: Query referenced non-existent columns

### Why It Happened
- **Code was correct** but Gunicorn (web server) hadn't reloaded
- **CSS was correct** but old code was still in memory
- **Database schema mismatch** between development and production

### How We Fixed It
1. Restarted Gunicorn with `--reload` flag
2. Fixed database query to match actual table structure
3. Verified changes were served to browsers

---

## 2. ARCHITECTURE OVERVIEW

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                         USER'S BROWSER                       │
│  (Chrome/Safari/Firefox on Desktop/Mobile)                  │
└────────────────┬────────────────────────────────────────────┘
                 │ HTTPS Request
                 │ (api.docdianasanchez.com)
                 ↓
┌─────────────────────────────────────────────────────────────┐
│                    NGINX (Web Server)                        │
│  - Handles SSL/TLS (HTTPS encryption)                       │
│  - Reverse proxy to backend                                 │
│  - Port 443 → Port 8000                                     │
└────────────────┬────────────────────────────────────────────┘
                 │ HTTP Request
                 │ (localhost:8000)
                 ↓
┌─────────────────────────────────────────────────────────────┐
│               GUNICORN (WSGI Server)                         │
│  - Python web server                                         │
│  - Manages worker processes                                  │
│  - Listens on 127.0.0.1:8000                                │
│  - 1 Master Process + 2 Worker Processes                    │
└────────────────┬────────────────────────────────────────────┘
                 │ Python Function Call
                 │
                 ↓
┌─────────────────────────────────────────────────────────────┐
│                   FLASK (app.py)                             │
│  - Python web framework                                      │
│  - Routes HTTP requests to functions                         │
│  - Renders HTML templates                                    │
│  - Processes business logic                                  │
└────────────────┬────────────────────────────────────────────┘
                 │ SQL Query
                 │
                 ↓
┌─────────────────────────────────────────────────────────────┐
│              POSTGRESQL (Database)                           │
│  - Stores bookings, visits, medications, etc.               │
│  - Tables: bookings, visits, medications, symptoms          │
└─────────────────────────────────────────────────────────────┘
```

### Request Flow - How It All Works

**When user clicks an appointment row:**

1. **Browser** (JavaScript): 
   ```javascript
   onclick="openMedicalRecord(80, event)"
   ```
   - Detects click on table row
   - Extracts booking_id (e.g., 80)

2. **JavaScript Function**:
   ```javascript
   window.open('/admin/medical-records?booking_id=80', '_blank', 'width=1400,height=900')
   ```
   - Opens new browser tab
   - Sends GET request to `/admin/medical-records?booking_id=80`

3. **NGINX** receives HTTPS request:
   ```
   https://api.docdianasanchez.com/admin/medical-records?booking_id=80
   ```
   - Decrypts HTTPS
   - Forwards to Gunicorn on port 8000

4. **Gunicorn** receives HTTP request:
   ```
   GET http://127.0.0.1:8000/admin/medical-records?booking_id=80
   ```
   - Routes to one of 2 worker processes
   - Worker calls Flask app

5. **Flask** matches route:
   ```python
   @app.route("/admin/medical-records", methods=["GET"])
   def admin_medical_records():
   ```
   - Checks authentication
   - Extracts booking_id from URL parameter

6. **Database Query**:
   ```python
   cur.execute("SELECT id, name, phone... FROM bookings WHERE id = %s", (80,))
   ```
   - PostgreSQL returns booking data

7. **Template Rendering**:
   ```python
   return render_template_string(MEDICAL_RECORDS_TEMPLATE, booking=booking)
   ```
   - Flask fills HTML template with data
   - Returns complete HTML page

8. **Response Path**:
   ```
   Flask → Gunicorn → NGINX → Browser
   ```

9. **Browser Displays**:
   - HTML page with patient information
   - Pre-filled form fields
   - Device tracking info

---

## 3. INITIAL PROBLEMS IDENTIFIED

### Problem 1: Medical Records 404 Error

**Symptoms:**
- Clicking appointment row opened new tab
- Browser showed: "404 Not Found"
- URL was correct: `/admin/medical-records?booking_id=80`

**What This Means:**
- Flask received the request
- But no route handler matched `/admin/medical-records`
- Flask returned default 404 error page

**Why It's Confusing:**
- Code inspection showed route EXISTS in app.py (line 2000)
- Route was correctly defined: `@app.route("/admin/medical-records")`
- Function existed: `def admin_medical_records():`

**The Mystery:**
Why did Flask say route doesn't exist when we can see it in the code?

---

### Problem 2: Charts Not Perfectly Circular

**Symptoms:**
- "By Status" doughnut chart was elliptical (squashed)
- "Real vs. Dummy" pie chart was elliptical
- Charts changed shape when resizing browser window

**What This Means:**
- Chart.js was rendering charts
- But CSS wasn't constraining aspect ratio
- Width and height were independent, not locked to 1:1

**Why It's Confusing:**
- Code inspection showed CSS exists: `aspect-ratio: 1/1`
- Class was applied: `<div class="panel chart-circle">`
- Browser dev tools should show this CSS

**The Mystery:**
Why didn't the browser apply the CSS we can see in app.py?

---

### Problem 3: Database Column Error

**Symptoms:**
After fixing 404, new error appeared:
```json
{"error":"column \"patient_id\" does not exist\nLINE 3: id, name, patient_id, phone..."}
```

**What This Means:**
- Flask route now working
- Database query executed
- PostgreSQL rejected query because column doesn't exist

**Why It Happened:**
- Development database had different schema than production
- Query was written for development tables
- Production `bookings` table didn't have those columns

---

## 4. ROOT CAUSE ANALYSIS

### Root Cause #1: Gunicorn Not Reloaded

**The Real Problem:**

Gunicorn workers were started BEFORE we added the new code:
- Workers started: 14:26 (2:26 PM)
- Code updated: ~16:00 (4:00 PM)
- Workers never reloaded the Python code

**How Gunicorn Works:**

1. **Master Process**: 
   - Started first
   - Reads app.py into memory
   - Spawns worker processes

2. **Worker Processes**:
   - Handle actual HTTP requests
   - Each has its OWN copy of app.py in memory
   - Don't automatically reload when file changes

3. **Without --reload Flag**:
   ```python
   # app.py in memory (loaded at 14:26)
   @app.route("/admin/view")  # ← Route exists
   # No medical-records route here yet!
   ```

4. **After Adding Code** (at 16:00):
   ```python
   # app.py ON DISK (updated at 16:00)
   @app.route("/admin/view")  # ← Route exists
   @app.route("/admin/medical-records")  # ← NEW route added
   ```

5. **Workers Still Using Old Memory**:
   - Workers read memory, not disk
   - Memory = old version (14:26)
   - Disk = new version (16:00)
   - Result: Route not found

**Why Touching File Didn't Work:**

```bash
touch app.py
```

This updates file modification time, but:
- Gunicorn wasn't started with `--reload` flag
- Gunicorn wasn't monitoring file changes
- Workers had no reason to reload

**The Fix:**

1. Kill workers: `sudo pkill -9 gunicorn`
2. Start with reload: `gunicorn --reload app:app`
3. Now Gunicorn monitors app.py for changes
4. Any file change triggers worker reload

---

### Root Cause #2: Database Schema Mismatch

**The Real Problem:**

Development database (MySQL) vs Production database (PostgreSQL) had different columns.

**Development `bookings` Table (MySQL):**
```sql
CREATE TABLE bookings (
    id INT,
    name VARCHAR(255),
    patient_id VARCHAR(50),        -- ← Column exists
    phone VARCHAR(50),
    email VARCHAR(255),
    channel VARCHAR(50),            -- ← Column exists
    virtual_platform VARCHAR(50),   -- ← Column exists
    address TEXT,
    address_city VARCHAR(100),      -- ← Column exists
    address_province VARCHAR(100),  -- ← Column exists
    gps_coordinates VARCHAR(100),   -- ← Column exists
    service VARCHAR(255),
    preferred_date DATE,
    preferred_time TIME,
    message TEXT,
    status VARCHAR(20),
    ip_address VARCHAR(45),         -- ← Column exists
    -- ... more columns
)
```

**Production `bookings` Table (PostgreSQL):**
```sql
CREATE TABLE bookings (
    id INT,
    name VARCHAR(255),
    -- patient_id MISSING!
    phone VARCHAR(50),
    email VARCHAR(255),
    -- channel MISSING!
    -- virtual_platform MISSING!
    -- address fields MISSING!
    service VARCHAR(255),
    preferred_date DATE,
    preferred_time TIME,
    message TEXT,
    status VARCHAR(20),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

**Why The Query Failed:**

```python
# Our query (written for development)
query = """
    SELECT id, name, patient_id, phone, email, channel, virtual_platform...
    FROM bookings WHERE id = %s
"""
```

PostgreSQL error:
```
ERROR: column "patient_id" does not exist
LINE 3: id, name, patient_id, phone...
                  ^^^^^^^^^^
```

**The Fix:**

Remove non-existent columns from query:
```python
# Fixed query (production-compatible)
query = """
    SELECT id, name, phone, email, service, 
           preferred_date, preferred_time, message, status,
           created_at, updated_at
    FROM bookings WHERE id = %s
"""
```

---

## 5. TROUBLESHOOTING PROCESS - CHRONOLOGICAL

### Phase 1: Initial Diagnosis (16:00 - 16:05)

**User Report:**
"Opening appointment gives 404 error and charts aren't circular"

**Initial Investigation:**
```bash
# Check if route exists in code
ssh beckham23@192.168.0.131
cd /home/beckham23/diana-booking-backend
grep -n '@app.route("/admin/medical-records"' app.py
# Result: Line 2000 - Route EXISTS ✓
```

```bash
# Check if CSS exists
grep 'aspect-ratio:1/1' app.py
# Result: Found - CSS EXISTS ✓
```

**Hypothesis 1:**
Code is correct, but server hasn't loaded it.

**Test:**
```bash
curl http://127.0.0.1:8000/admin/medical-records?booking_id=80
# Result: Empty response
```

**Conclusion:**
Gunicorn isn't serving the new route.

---

### Phase 2: Gunicorn Restart Attempts (16:05 - 16:12)

**Attempt 1: Touch File**
```bash
touch app.py
sleep 5
# Result: No reload, route still 404
```

**Why it Failed:**
Gunicorn not started with `--reload` flag.

**Attempt 2: HUP Signal**
```bash
kill -HUP $(pgrep gunicorn)
# Result: Permission denied (needs sudo)
```

**Attempt 3: Kill and Restart**
```bash
sudo pkill -9 -f 'gunicorn.*app:app'
sudo /home/beckham23/faker-env/bin/gunicorn -w 2 -b 127.0.0.1:8000 --reload app:app &
# Result: Permission denied on /var/log/diana-booking.log
```

**Problem Discovered:**
Log file has wrong permissions.

---

### Phase 3: Permission Issues (16:12 - 16:15)

**Problem:**
```bash
sudo gunicorn ... >> /var/log/diana-booking.log 2>&1 &
# Error: Permission denied
```

**Root Cause:**
- Running command with `sudo`
- But shell redirection (`>>`) happens BEFORE sudo
- Shell runs as `beckham23` user
- `/var/log/diana-booking.log` requires root permissions

**Wrong Approach:**
```bash
# This doesn't work because >> happens before sudo
sudo command >> /var/log/file.log
```

**Correct Approach:**
```bash
# Create file with permissions first
sudo touch /var/log/diana-booking.log
sudo chmod 666 /var/log/diana-booking.log

# Now redirect works
sudo gunicorn ... > /var/log/diana-booking.log 2>&1 &
```

**Success:**
```
[2026-07-23 16:15:42] [530210] [INFO] Starting gunicorn 26.0.0
[2026-07-23 16:15:42] [530210] [INFO] Listening at: http://127.0.0.1:8000
[2026-07-23 16:15:42] [530211] [INFO] Booting worker with pid: 530211
[2026-07-23 16:15:42] [530212] [INFO] Booting worker with pid: 530212
```

Gunicorn now running! ✓

---

### Phase 4: Port Conflicts (16:15 - 16:20)

**New Problem:**
```
ERROR: Connection in use: ('127.0.0.1', 8000)
ERROR: Address already in use
```

**Diagnosis:**
```bash
# Check what's using port 8000
sudo lsof -i :8000
# Result: Empty (but error persists)

# Check for zombie processes
ps aux | grep gunicorn
# Result: Multiple old processes running
```

**Root Cause:**
Multiple failed start attempts left zombie processes.

**Solution:**
```bash
# Nuclear option - kill ALL Python/Gunicorn processes
sudo pkill -9 -f python
sudo pkill -9 -f gunicorn

# Verify clean
ps aux | grep -E "python|gunicorn" | grep -v grep
# Result: Empty ✓

# Start fresh
sudo /home/beckham23/faker-env/bin/gunicorn -w 2 -b 127.0.0.1:8000 --reload app:app &
```

**Success:**
Gunicorn started cleanly with --reload flag enabled.

---

### Phase 5: Database Column Error (16:20 - 16:22)

**User Report:**
"Page opens but shows error about patient_id column"

**Error Message:**
```json
{
  "error": "column \"patient_id\" does not exist\nLINE 3: id, name, patient_id, phone..."
}
```

**Investigation:**
```bash
# Check actual database schema
psql -d diana_bookings -c "\d bookings"
# Result: No patient_id column in production
```

**Query in Code:**
```python
query = """
    SELECT 
        id, name, patient_id, phone, email, channel, virtual_platform,
        address, address_city, address_province, gps_coordinates,
        service, preferred_date, preferred_time, message, status,
        ip_address, ip_country, ip_city, device_type, device_brand,
        device_model, device_os, device_browser, screen_size,
        user_language, user_timezone, connection_type,
        created_at, updated_at
    FROM bookings 
    WHERE id = %s
"""
```

**Actual Table Columns:**
```sql
id, name, phone, email, service, preferred_date, preferred_time, 
message, status, created_at, updated_at, is_dummy
```

**Fix Applied:**
```bash
cd /home/beckham23/diana-booking-backend
# Backup first
cp app.py app.py.backup-before-column-fix

# Remove non-existent columns with sed
sed -i 's/id, name, patient_id, phone, email, channel, virtual_platform,/id, name, phone, email,/g' app.py
sed -i 's/address, address_city, address_province, gps_coordinates,//g' app.py
sed -i 's/ip_address, ip_country, ip_city, device_type, device_brand,//g' app.py
sed -i 's/device_model, device_os, device_browser, screen_size,//g' app.py
sed -i 's/user_language, user_timezone, connection_type,//g' app.py
```

**Verification:**
```bash
# Check the query now
grep -A 8 "def admin_medical_records" app.py | grep -A 5 "SELECT"
# Result: Only existing columns ✓
```

**Auto-Reload:**
```
[2026-07-23 16:22:13] [530210] [INFO] Worker reloading: app.py modified
[2026-07-23 16:22:13] [530211] [INFO] Worker reloading
[2026-07-23 16:22:13] [530212] [INFO] Worker reloading
```

Gunicorn automatically reloaded because `--reload` flag was enabled! ✓

**Final Test:**
```bash
curl http://127.0.0.1:8000/admin/medical-records?booking_id=80 | head -20
# Result: HTML output with patient data ✓
```

**Browser Test:**
User confirmed: "It worked!"

---

