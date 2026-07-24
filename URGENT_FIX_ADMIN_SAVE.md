# URGENT: Fix Admin Medical Records Save Issue

## Problem
**Error:** `Failed to load resource: net::ERR_BLOCKED_BY_CLIENT`  
**Impact:** Cannot save medical records

---

## Root Cause
Browser ad blocker/privacy extension is blocking API requests

---

## Immediate Solution (User Side)

### Option 1: Whitelist in Ad Blocker

**uBlock Origin:**
1. Click uBlock icon in toolbar
2. Click the blue power button (will turn gray)
3. Refresh page

**AdBlock Plus:**
1. Click AdBlock icon
2. Select "Don't run on pages on this domain"
3. Refresh page

### Option 2: Test in Incognito/Private Mode
1. Open new Incognito window (Cmd/Ctrl + Shift + N)
2. Navigate to admin page
3. Extensions are usually disabled here

---

## Permanent Fix (Developer Side)

### 1. Add Proper CORS Headers in Backend

**File:** `backend/app.py`

Add this at the top after imports:

```python
from flask_cors import CORS

# After app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://docdianasanchez.com",
            "https://api.docdianasanchez.com"
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        "allow_headers": ["Content-Type", "X-Admin-Token"],
        "supports_credentials": True
    }
})
```

**Install flask-cors:**
```bash
ssh beckham23@192.168.0.131
cd diana-booking-backend
pip3 install flask-cors
# Add to requirements.txt
echo "flask-cors==4.0.0" >> requirements.txt
```

### 2. Rename Suspicious Endpoints

Ad blockers flag URLs containing "ad", "track", "analytics", etc.

**Current problematic patterns:**
- `/api/admin/...` ← Contains "ad"

**Solution:** Use alternative names internally or accept the limitation

---

## Testing Commands

### Test from command line (no ad blocker):
```bash
# Test API health
curl https://api.docdianasanchez.com/api/health

# Test with auth token (replace TOKEN)
curl -X PUT https://api.docdianasanchez.com/api/admin/visits/123 \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: YOUR_TOKEN" \
  -d '{"chief_complaint":"test"}'
```

### Check browser console:
1. Open DevTools (F12)
2. Go to Network tab
3. Try to save
4. Look for blocked requests (will show in red)
5. Click on blocked request
6. Check "Initiator" column - shows which extension blocked it

---

## Deploy Updated Backend

```bash
# 1. Add CORS support
ssh beckham23@192.168.0.131
cd diana-booking-backend
pip3 install flask-cors
echo "flask-cors==4.0.0" >> requirements.txt

# 2. Update app.py with CORS config
# (edit app.py on server or upload from local)

# 3. Restart backend
bash restart_backend.sh

# 4. Test
curl https://api.docdianasanchez.com/api/health
```

---

## Alternative: Use Backend-Served Admin

Instead of using GitHub Pages admin, access the backend-served version:

**URL:** `https://api.docdianasanchez.com/admin/view`

This version is served directly by Flask, so:
- No CORS issues
- Same domain for frontend and backend
- Less likely to be blocked by ad blockers

---

## Status Check

**Current Status:**
- ❌ Medical records not saving (blocked by ad blocker)
- ✅ Backend endpoint exists and is correct
- ✅ Frontend makes correct API calls
- ❌ CORS headers may need improvement
- ❓ Frontend admin at `/admin/` status unknown

**Next Actions:**
1. User: Disable ad blocker for testing
2. Developer: Add proper CORS headers
3. Test both admin interfaces
4. Deploy fixes

---

## For User (Quick Fix Now)

**Right now, to save medical records:**

1. Open browser DevTools (F12)
2. Go to Console tab
3. Look for errors mentioning "blocked"
4. Disable the blocking extension
5. Refresh page
6. Try saving again

**OR**

Use a different browser without extensions installed (Safari, Edge, etc.)

---

Last updated: 2026-07-24
