# 🔄 Backend Restart Instructions

## Current Situation

The backend API has been updated with the GET endpoint for `/api/bookings`, but the Gunicorn service needs to be restarted to load the new code.

**Status**:
- ✅ New code uploaded to server
- ✅ Database has 80 bookings ready
- ⏳ Gunicorn needs restart (requires sudo)

---

## Quick Restart (Recommended)

### Option 1: Using the restart script

```bash
# SSH into server
ssh beckham23@192.168.0.131

# Run restart script with sudo
sudo bash ~/diana-booking-backend/restart_backend.sh
```

Enter your password when prompted, and the script will:
1. Stop old Gunicorn processes
2. Start new Gunicorn with updated code
3. Test the API automatically
4. Show bookings data

---

## Manual Restart Steps

If the script doesn't work, do it manually:

### Step 1: SSH into server
```bash
ssh beckham23@192.168.0.131
```

### Step 2: Stop Gunicorn (requires sudo)
```bash
sudo pkill -f "gunicorn.*app:app"
```

### Step 3: Wait a moment
```bash
sleep 2
```

### Step 4: Start Gunicorn
```bash
cd ~/diana-booking-backend
sudo nohup ~/faker-env/bin/gunicorn -w 2 -b 127.0.0.1:8000 --reuse-port app:app > gunicorn.log 2>&1 &
```

### Step 5: Verify it's running
```bash
ps aux | grep gunicorn
```

You should see 2-3 gunicorn processes.

### Step 6: Test the API
```bash
# Health check
curl http://localhost:8000/api/health

# Get bookings
curl http://localhost:8000/api/bookings | python3 -m json.tool | head -50
```

---

## Verify Admin Panel Works

After restarting the backend:

### 1. Test API from your computer
```bash
curl https://api.docdianasanchez.com/api/bookings | jq '.' | head -50
```

### 2. Open Admin Panel
Visit: https://docdianasanchez.com/admin/

**Login**: `diana2024`

### 3. Check Appointments Tab
- Should see all 80 appointments from database
- Each appointment should show device tracking info
- Status updates should sync to database

---

## Expected Results

After restart, the admin panel should show:

### Appointments Display
```
┌─────────────────────────────────────────┐
│ Appointments (80)                        │
├─────────────────────────────────────────┤
│ ● oscar s                                │
│   📞 7171717171                          │
│   🌐 IP: xxx.xxx.xxx.xxx · Location     │
│   📱 Device: mobile · Brand              │
│   💻 OS: iOS 17.2 · Safari               │
│   Status: pending                        │
├─────────────────────────────────────────┤
│ ● jjjjjj                                 │
│   📞 7777777777                          │
│   ...                                    │
└─────────────────────────────────────────┘
```

---

## Troubleshooting

### Issue: "Permission denied" when running pkill

**Solution**: Use `sudo`
```bash
sudo pkill -f "gunicorn.*app:app"
```

### Issue: Gunicorn won't stop

**Solution**: Force kill
```bash
sudo pkill -9 -f "gunicorn.*app:app"
```

### Issue: API still returns 405 error

**Solution**: Check if old process is still running
```bash
ps aux | grep gunicorn
# If you see old processes, kill them:
sudo kill -9 <PID>
```

### Issue: Admin panel still shows no data

**Check**:
1. API is actually restarted:
   ```bash
   curl http://localhost:8000/api/bookings | head
   ```

2. Browser console (F12) for errors

3. Try hard refresh: `Cmd + Shift + R` (Mac) or `Ctrl + Shift + R` (Windows)

### Issue: Can't connect to server

**Solution**: Verify SSH access
```bash
ssh beckham23@192.168.0.131
# If this works, you're good. If not, check:
# - Server is online
# - SSH keys are set up
# - Network connection
```

---

## Alternative: Restart via systemd

If there's a systemd service configured:

```bash
# Check if service exists
sudo systemctl list-units | grep diana

# Restart service
sudo systemctl restart diana-booking

# Check status
sudo systemctl status diana-booking

# View logs
sudo journalctl -u diana-booking -f
```

---

## What Changed in the New Code

The updated `app.py` now includes:

### New Endpoint: GET /api/bookings
```python
@app.route('/api/bookings', methods=['GET', 'POST'])
def handle_bookings():
    if request.method == 'GET':
        # Fetch all bookings from database
        # Returns JSON with bookings array
```

### Key Features:
- ✅ PostgreSQL support (not MySQL)
- ✅ Fetches all bookings from database
- ✅ Includes device tracking info
- ✅ Filter by status: `?status=pending`
- ✅ Returns proper JSON format
- ✅ CORS configured for frontend

### Database Columns Retrieved:
- Basic info: id, name, phone, email
- Appointment: service, date, time, status
- Location: address, city, province, GPS
- Tracking: IP, device, OS, browser
- Timestamps: created_at, updated_at

---

## Testing Checklist

After restart, verify:

- [ ] `curl http://localhost:8000/api/health` returns `{"status":"ok","db":"up"}`
- [ ] `curl http://localhost:8000/api/bookings` returns JSON array
- [ ] Admin panel at https://docdianasanchez.com/admin/ shows appointments
- [ ] Appointment cards show device tracking info
- [ ] Status updates work (confirm/cancel buttons)
- [ ] No console errors in browser

---

## Quick Commands Reference

```bash
# SSH to server
ssh beckham23@192.168.0.131

# Restart backend (easy way)
sudo bash ~/diana-booking-backend/restart_backend.sh

# Check if running
ps aux | grep gunicorn

# Test API
curl http://localhost:8000/api/health
curl http://localhost:8000/api/bookings | head -100

# View logs
tail -50 ~/diana-booking-backend/gunicorn.log

# View real-time logs
tail -f ~/diana-booking-backend/gunicorn.log
```

---

## Next Steps After Restart

1. **Test Admin Panel**
   - Login and verify appointments load
   - Check device tracking displays correctly
   - Test status updates

2. **Submit Test Booking**
   - Go to https://docdianasanchez.com
   - Fill out booking form
   - Check it appears in admin panel immediately

3. **Monitor Logs**
   ```bash
   ssh beckham23@192.168.0.131
   tail -f ~/diana-booking-backend/gunicorn.log
   ```

4. **Update Frontend If Needed**
   - If admin panel still doesn't work, check `admin/admin.js`
   - Verify API_URL is correct

---

## Support

If you encounter issues:

1. **Check Logs**
   ```bash
   tail -50 ~/diana-booking-backend/gunicorn.log
   ```

2. **Verify Database**
   ```bash
   python3 -c "import psycopg2; print('DB connected')"
   ```

3. **Test Manually**
   ```bash
   cd ~/diana-booking-backend
   python3 app.py
   # Then Ctrl+C and restart with gunicorn
   ```

4. **Contact Developer**
   - Julian Sanchez
   - Check error messages in logs
   - Provide output of test commands

---

## Summary

**What You Need to Do**:
```bash
ssh beckham23@192.168.0.131
sudo bash ~/diana-booking-backend/restart_backend.sh
```

**What Will Happen**:
1. Old Gunicorn processes stopped
2. New code loaded
3. API starts with GET /api/bookings endpoint
4. Admin panel can now fetch 80 bookings from database

**Result**:
✅ Admin panel will show all appointments with device tracking info!

---

*Last updated: July 23, 2026*
