# 🚀 RESTART BACKEND NOW

## Quick Fix for Admin Panel

The admin panel isn't showing appointments because the backend needs to be restarted with the new code.

---

## ⚡ Quick Fix (2 minutes)

Open Terminal and run these commands:

```bash
ssh beckham23@192.168.0.131
sudo bash ~/diana-booking-backend/restart_backend.sh
```

Enter your password when prompted.

**That's it!** 

The script will:
1. ✅ Stop old backend
2. ✅ Start new backend with updated code  
3. ✅ Test the API
4. ✅ Show you it's working

---

## 📊 What You'll See

After running the script, you should see:

```
🔄 Restarting Dr. Diana Sánchez Backend API...
Stopping old Gunicorn processes...
Starting new Gunicorn server...
✅ Backend restarted successfully!

Testing API...
{"status":"ok","db":"up"}

Checking bookings endpoint...
{"ok":true,"bookings":[{"id":80,"name":"oscar s",...
```

---

## 🎯 Verify It Works

1. **Check Admin Panel**
   - Go to: https://docdianasanchez.com/admin/
   - Login: `diana2024`
   - You should now see 80 appointments!

2. **Each appointment should show**:
   - Patient name and contact info
   - 🌐 IP address and location
   - 📱 Device type and brand
   - 💻 Operating system and browser

---

## 🆘 If Something Goes Wrong

### Option 1: Manual Restart
```bash
ssh beckham23@192.168.0.131
sudo pkill -f gunicorn
cd ~/diana-booking-backend
sudo nohup ~/faker-env/bin/gunicorn -w 2 -b 127.0.0.1:8000 --reuse-port app:app > gunicorn.log 2>&1 &
```

### Option 2: Check What's Wrong
```bash
ssh beckham23@192.168.0.131
tail -50 ~/diana-booking-backend/gunicorn.log
```

---

## 📝 Why This Is Needed

- ✅ New code uploaded to server
- ✅ Database has 80 bookings ready
- ✅ Admin panel code updated
- ⏳ **Backend needs restart to load new API endpoint**

The new code adds `GET /api/bookings` endpoint that the admin panel uses to fetch appointments from the database.

---

## 📚 More Details

See: `BACKEND_RESTART_INSTRUCTIONS.md` for comprehensive guide.

---

**Status**: Ready to restart  
**Time needed**: 2 minutes  
**Risk**: Low (can rollback if needed)  
**Impact**: Admin panel will show all appointments

**Do it now!** 🚀
