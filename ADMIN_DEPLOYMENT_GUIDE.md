# Admin Panel Deployment Guide

## Overview
The admin panel is served from **two locations**:

1. **Backend Admin** (Medical Records): `https://api.docdianasanchez.com/admin/view`
   - Served by Flask backend
   - Uses backend authentication
   
2. **Frontend Admin** (Reviews): `https://docdianasanchez.com/admin/`
   - Served by GitHub Pages
   - Calls backend API at `api.docdianasanchez.com`

---

## Current Issue: Medical Records Not Saving

### Error: `ERR_BLOCKED_BY_CLIENT`

**Cause:** Browser extension (ad blocker) blocking requests

**Solution:**
1. Whitelist both domains in your ad blocker:
   - `docdianasanchez.com`
   - `api.docdianasanchez.com`
2. Or test in Incognito mode (extensions disabled)

**How to whitelist in uBlock Origin:**
1. Click uBlock icon
2. Click the power button to disable for site
3. Refresh page

---

## Deployment Locations

### 1. Backend Files (Proxmox Server)

**Server:** `beckham23@192.168.0.131`  
**Path:** `/home/beckham23/diana-booking-backend/`

```bash
# Main application
backend/app.py                          → /home/beckham23/diana-booking-backend/app.py
backend/notify.py                       → /home/beckham23/diana-booking-backend/notify.py
backend/requirements.txt                → /home/beckham23/diana-booking-backend/requirements.txt

# Static files served by backend
admin/medical-records.js                → /home/beckham23/diana-booking-backend/static/medical-records.js
admin/medical-records.html              → /home/beckham23/diana-booking-backend/static/medical-records.html
backend/medical_records_template.html   → /home/beckham23/diana-booking-backend/medical_records_template.html
```

**Deploy command:**
```bash
scp backend/app.py beckham23@192.168.0.131:/home/beckham23/diana-booking-backend/
scp admin/medical-records.js beckham23@192.168.0.131:/home/beckham23/diana-booking-backend/static/
ssh beckham23@192.168.0.131 "cd diana-booking-backend && bash restart_backend.sh"
```

### 2. Frontend Files (GitHub Pages)

**Repo:** `https://github.com/sancho16/docDianaSanchez`  
**Branch:** `main`  
**GitHub Pages serves from root**

```bash
# Admin panel (review management)
admin/index.html                        → GitHub Pages
admin/admin.css                         → GitHub Pages
admin/admin.js                          → GitHub Pages

# Main site
index.html                              → GitHub Pages
css/                                    → GitHub Pages
js/                                     → GitHub Pages
assets/                                 → GitHub Pages
```

**Deploy command:**
```bash
git add admin/
git commit -m "Update admin panel"
git push origin main
# GitHub Pages auto-deploys in ~1 minute
```

---

## Admin Panel Access Points

### Medical Records (Backend)
- **URL:** `https://api.docdianasanchez.com/admin/view`
- **Purpose:** View/manage patient medical records
- **Auth:** Backend cookie authentication
- **Data:** Direct database access

### Review Management (Frontend)
- **URL:** `https://docdianasanchez.com/admin/`
- **Purpose:** Manage patient reviews
- **Auth:** Password login (calls backend API)
- **Data:** API calls to `api.docdianasanchez.com`

---

## Fixing Review Admin at docdianasanchez.com/admin/

### Current Issue
The page loads but doesn't open/function properly.

### Check List

1. **Verify files are deployed to GitHub:**
   ```bash
   # Check GitHub repo has latest files
   git status
   git log --oneline -5
   ```

2. **Check API endpoint in admin.js:**
   ```javascript
   // Should point to:
   const API_BASE = 'https://api.docdianasanchez.com';
   ```

3. **Check CORS headers in backend:**
   ```python
   # In app.py, should have:
   @app.after_request
   def after_request(response):
       response.headers['Access-Control-Allow-Origin'] = 'https://docdianasanchez.com'
       response.headers['Access-Control-Allow-Credentials'] = 'true'
       return response
   ```

4. **Test API is accessible:**
   ```bash
   curl https://api.docdianasanchez.com/api/health
   ```

---

## Testing Checklist

### Backend Medical Records
- [ ] Can access `https://api.docdianasanchez.com/admin/view`
- [ ] Login page appears
- [ ] Can authenticate
- [ ] Can view booking cards
- [ ] Can open medical record
- [ ] Can save progress (no ERR_BLOCKED_BY_CLIENT)
- [ ] Can complete visit

### Frontend Review Admin
- [ ] Can access `https://docdianasanchez.com/admin/`
- [ ] Login page appears
- [ ] Can authenticate
- [ ] Reviews load from API
- [ ] Can add/edit/delete reviews
- [ ] No CORS errors in console

---

## Common Issues & Fixes

### Issue: ERR_BLOCKED_BY_CLIENT
**Solution:** Disable ad blocker for both domains

### Issue: CORS errors
**Solution:** Add proper CORS headers in backend app.py

### Issue: 401 Unauthorized
**Solution:** Check authentication token in cookies

### Issue: 502 Bad Gateway
**Solution:** Backend not running, restart it

### Issue: Changes not visible
**Solution:** 
- Backend: Restart service
- Frontend: Wait 1 min for GitHub Pages, hard refresh (Cmd+Shift+R)

---

## Quick Deploy Script

Save as `deploy.sh`:

```bash
#!/bin/bash

echo "🚀 Deploying Admin Panel..."

# Deploy backend
echo "📦 Deploying backend..."
scp backend/app.py beckham23@192.168.0.131:/home/beckham23/diana-booking-backend/
scp admin/medical-records.js beckham23@192.168.0.131:/home/beckham23/diana-booking-backend/static/

# Restart backend
echo "🔄 Restarting backend..."
ssh beckham23@192.168.0.131 "cd diana-booking-backend && bash restart_backend.sh"

# Deploy frontend
echo "🌐 Deploying frontend..."
git add .
git commit -m "Update admin panel"
git push origin main

echo "✅ Deployment complete!"
echo "Backend: https://api.docdianasanchez.com/admin/view"
echo "Frontend: https://docdianasanchez.com/admin/"
echo "⏳ GitHub Pages will update in ~1 minute"
```

---

## Next Steps

1. **Fix ERR_BLOCKED_BY_CLIENT:** Whitelist domains in ad blocker
2. **Test medical records save:** Try in Incognito mode
3. **Fix frontend admin:** Check why it doesn't open properly
4. **Deploy both:** Use commands above

---

**Need help?** Check browser console (F12) for specific error messages.
