# 🔧 MANUAL FIX INSTRUCTIONS
## Fix Medical Records 404 Error and Perfect Circle Charts

---

## ⚠️ PROBLEM
1. **Medical Records page returns 404** - Route exists in code but Gunicorn hasn't loaded it
2. **Charts not circular** - CSS exists in code but not being served

## ✅ SOLUTION
The code is correct, but Gunicorn workers need a full restart to load the new route.

---

## 🛠️ STEP-BY-STEP FIX

### Option 1: Full Restart (Recommended)

**SSH into the server:**
```bash
ssh beckham23@192.168.0.131
```

**Stop Gunicorn:**
```bash
sudo pkill -9 -f 'gunicorn.*app:app'
```

**Wait 2 seconds:**
```bash
sleep 2
```

**Start Gunicorn with --reload flag:**
```bash
cd /home/beckham23/diana-booking-backend
sudo nohup /home/beckham23/faker-env/bin/gunicorn -w 2 -b 127.0.0.1:8000 --reload app:app >> /var/log/diana-booking.log 2>&1 &
```

**Verify it's running:**
```bash
ps aux | grep gunicorn | grep -v grep
```

**You should see 3 processes** (1 master + 2 workers)

---

### Option 2: If Using Systemd

```bash
sudo systemctl restart diana-booking-backend
sudo systemctl status diana-booking-backend
```

---

### Option 3: If Using Supervisor

```bash
sudo supervisorctl restart diana-booking-backend
sudo supervisorctl status diana-booking-backend
```

---

## 🧪 TEST THE FIX

### Test 1: Check Route Exists
```bash
curl -I http://127.0.0.1:8000/admin/medical-records?booking_id=80
```

**Expected**: `HTTP/1.1 302` or `401` (redirect to login - this is GOOD)  
**Bad**: `HTTP/1.1 404` (route not found)

### Test 2: Check Admin Panel
Visit: https://api.docdianasanchez.com/admin/view

1. Log in
2. **Check charts** - Should be perfect circles
3. **Click appointment row** - Should open medical records in new tab
4. **Medical records should load** (not 404)

---

## 🔍 VERIFY CHANGES ARE IN APP.PY

```bash
cd /home/beckham23/diana-booking-backend

# Check route exists
grep -c '@app.route("/admin/medical-records"' app.py
# Should output: 1

# Check CSS exists  
grep -c 'aspect-ratio:1/1' app.py
# Should output: 1

# Check chart-circle class applied
grep -c 'panel chart-circle' app.py
# Should output: 2 or more
```

---

## 🐛 IF STILL NOT WORKING

### Check Nginx/Proxy Logs
```bash
sudo tail -50 /var/log/nginx/error.log
sudo tail -50 /var/log/nginx/access.log
```

### Check Gunicorn Logs
```bash
tail -100 /var/log/diana-booking.log
# or
journalctl -u diana-booking-backend -n 100
```

### Check Python Import Errors
```bash
cd /home/beckham23/diana-booking-backend
/home/beckham23/faker-env/bin/python3 -c "import app; print('✓ App loads successfully')"
```

### Manual Test the Route
```bash
cd /home/beckham23/diana-booking-backend
/home/beckham23/faker-env/bin/python3 << 'PYEOF'
from app import app
with app.test_client() as client:
    response = client.get('/admin/medical-records?booking_id=80')
    print(f"Status: {response.status_code}")
    if response.status_code == 404:
        print("❌ Route not found!")
        # List all routes
        print("Available routes:")
        for rule in app.url_map.iter_rules():
            print(f"  {rule}")
    else:
        print("✓ Route exists!")
PYEOF
```

---

## 📱 CLEAR BROWSER CACHE

The charts CSS might be cached in your browser:

### On Desktop:
- **Chrome/Edge**: Ctrl+Shift+Delete (Windows) or Cmd+Shift+Delete (Mac)
- **Firefox**: Ctrl+Shift+Delete (Windows) or Cmd+Shift+Delete (Mac)
- **Safari**: Cmd+Option+E

### Force Reload:
- **Windows**: Ctrl+Shift+R
- **Mac**: Cmd+Shift+R

### Or Use Incognito/Private Mode:
- **Chrome**: Ctrl+Shift+N (Windows) or Cmd+Shift+N (Mac)
- **Firefox**: Ctrl+Shift+P (Windows) or Cmd+Shift+P (Mac)
- **Safari**: Cmd+Shift+N

---

## 🎯 QUICK FIX COMMANDS (Copy-Paste)

```bash
# All-in-one fix command
ssh beckham23@192.168.0.131 << 'REMOTE'
cd /home/beckham23/diana-booking-backend
echo "Stopping Gunicorn..."
sudo pkill -9 -f 'gunicorn.*app:app'
sleep 3
echo "Starting Gunicorn with --reload..."
sudo nohup /home/beckham23/faker-env/bin/gunicorn -w 2 -b 127.0.0.1:8000 --reload app:app >> /var/log/diana-booking.log 2>&1 &
sleep 3
echo "Testing route..."
curl -I http://127.0.0.1:8000/admin/medical-records?booking_id=80 2>&1 | head -1
echo "Done! Now test in browser."
REMOTE
```

---

## ✅ SUCCESS INDICATORS

After the fix, you should see:

### In Browser:
1. ✅ Charts at https://api.docdianasanchez.com/admin/view are perfect circles
2. ✅ Clicking appointment row opens new tab
3. ✅ Medical records page loads (not 404)
4. ✅ Patient data is pre-filled

### In Terminal:
```bash
$ curl -I http://127.0.0.1:8000/admin/medical-records?booking_id=80
HTTP/1.1 302 FOUND  # ← This is GOOD (redirect to login)
# or
HTTP/1.1 401 UNAUTHORIZED  # ← This is also GOOD (needs auth)
```

**NOT**:
```bash
HTTP/1.1 404 NOT FOUND  # ← This is BAD (route not loaded)
```

---

## 📞 STILL HAVING ISSUES?

### Worst Case Scenario - Rollback:
```bash
cd /home/beckham23/diana-booking-backend
# Find latest backup
ls -lth app.py.backup-* | head -1
# Restore it
cp app.py.backup-YYYYMMDD-HHMMSS app.py
# Restart
sudo pkill -9 -f 'gunicorn'; sleep 2; sudo nohup /home/beckham23/faker-env/bin/gunicorn -w 2 -b 127.0.0.1:8000 app:app &
```

### Contact Support:
- Check GitHub: https://github.com/sancho16/docDianaSanchez
- Review: ADMIN_VIEW_UPDATES.md
- Check: DEPLOYMENT_UPDATE_JUL23_2026.md

---

**Last Updated**: July 23, 2026  
**Status**: Awaiting Server Restart
