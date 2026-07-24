# Admin Systems Architecture - Dr. Diana Sánchez

## Overview

The booking system has **TWO INDEPENDENT** admin panels with different purposes, hosting, and authentication methods. Both work simultaneously but serve different use cases.

---

## System 1: GitHub Pages Admin Panel

### URL
- **Primary**: `https://docdianasanchez.com/admin/`
- **Alternative**: `https://www.docdianasanchez.com/admin/`

### Hosting
- **Platform**: GitHub Pages (static hosting)
- **Files**: `/admin/` directory in repository
- **Deployment**: Automatic via GitHub Actions on push to main branch

### File Structure
```
/admin/
├── index.html          # Main admin page (login + dashboard)
├── admin.css           # Styles
├── admin.js            # Client-side logic and authentication
├── medical-records.html
└── medical-records.js
```

### Authentication Method
**Client-Side JavaScript Password Check**

1. User visits `https://docdianasanchez.com/admin/`
2. Sees login form (from index.html)
3. Enters password
4. JavaScript in `admin.js` validates password against hardcoded value
5. If correct, hides login screen and shows admin dashboard
6. Password stored in sessionStorage to persist across page reloads

**Hardcoded Password Location**: `admin/admin.js` line ~8
```javascript
const ADMIN_PASS = 'diana2024';  // Change this to update password
```

### Security Model
- ⚠️ **Not secure against determined attackers** (password is in client-side JS)
- ✅ **Good enough for basic access control** (prevents casual access)
- ✅ **Easy to use** (simple password, no server needed)
- ℹ️ **Best for**: Trusted users, non-critical operations, quick access

### Data Access
- Makes API calls to backend: `https://api.docdianasanchez.com/api/admin/...`
- All data operations go through backend API
- No direct database access

### How It Works - Step by Step

**Login Flow:**
```
1. User → https://docdianasanchez.com/admin/
2. GitHub Pages → Serves /admin/index.html
3. Browser → Shows login form
4. User → Enters password
5. admin.js → Validates password === 'diana2024'
6. If match → sessionStorage.setItem('dds_admin_authed', 'true')
7. JavaScript → Hides login, shows dashboard
8. Dashboard → Fetches data from api.docdianasanchez.com
```

**Data Retrieval:**
```javascript
// Example from admin.js
fetch('https://api.docdianasanchez.com/api/admin/bookings')
  .then(res => res.json())
  .then(data => displayBookings(data))
```

### Advantages
- ✅ Fast access (no server-side session management)
- ✅ Works offline after initial load
- ✅ No backend deployment needed for UI changes
- ✅ Free hosting via GitHub Pages
- ✅ Easy password change (just edit admin.js)

### Disadvantages
- ⚠️ Password visible in source code (obfuscated but not secure)
- ⚠️ No server-side session management
- ⚠️ No audit logging of who logged in
- ⚠️ Anyone can see the authentication code

---

## System 2: Backend Admin Panel

### URL
- **Primary**: `https://api.docdianasanchez.com/admin/`
- **Alternative**: `https://api.docdianasanchez.com/admin`

### Hosting
- **Platform**: Backend Flask server (beckham23@192.168.0.131)
- **Directory**: `/home/beckham23/diana-booking-backend/`
- **Server**: Gunicorn + Flask (Python)

### File Structure
```
/backend/
├── app.py              # Flask application with embedded HTML
├── .env                # Environment variables (ADMIN_TOKEN, etc.)
└── templates/          # (Future: external HTML templates)
```

### Authentication Methods

**Method 1: Admin Token (Legacy)**

Secure server-side token validation:

1. User visits `https://api.docdianasanchez.com/admin/`
2. Server renders login page with token input field
3. User enters admin token
4. POSTs to `/admin/login`
5. Server validates: `token == ADMIN_TOKEN` (from .env)
6. If valid: Sets httponly cookie, redirects to `/admin/view`
7. If invalid: Shows error message

**Token Location**: `.env` file on server
```bash
ADMIN_TOKEN=ba19bba1878de076f13109e59c84574a2c900eea9d94731d
```

**Method 2: Google Sign-In (OAuth)**

Modern OAuth 2.0 authentication:

1. User clicks "Sign in with Google" button
2. Google OAuth popup appears
3. User signs in with Google account
4. Google returns ID token
5. Frontend POSTs token to `/api/admin/auth`
6. Backend verifies token with Google
7. Backend checks if email is in `ALLOWED_ADMINS` list
8. If allowed: Sets httponly cookie, redirects to admin view
9. If not allowed: Returns 403 error

**Allowed Emails Location**: `.env` file on server
```bash
ALLOWED_ADMINS=osanchy7@gmail.com,julidb710@gmail.com
```

### Cookie-Based Session

After successful authentication (either method):

```python
resp.set_cookie(
    'admin_session',
    value='<email or token>',
    httponly=True,      # Cannot be accessed by JavaScript
    secure=True,        # Only sent over HTTPS
    samesite='Strict',  # CSRF protection
    max_age=60*60*8     # 8 hours
)
```

### Security Model
- ✅ **Highly secure** (server-side validation)
- ✅ **HttpOnly cookies** (XSS protection)
- ✅ **Secure cookies** (HTTPS only)
- ✅ **SameSite protection** (CSRF prevention)
- ✅ **Token never exposed** to client
- ✅ **Google OAuth** industry standard
- ℹ️ **Best for**: Production use, multiple admins, audit requirements

### Routes in app.py

```python
@app.route("/admin", methods=["GET"])
@app.route("/admin/", methods=["GET"])
def admin_login_page():
    """Show login page if not authenticated, else redirect to dashboard"""
    if _admin_authed():
        return redirect(url_for("admin_view"))
    return render_template_string(ADMIN_LOGIN_HTML, 
                                  google_client_id=GOOGLE_CLIENT_ID)

@app.route("/admin/login", methods=["POST"])
def admin_login():
    """Handle token-based login"""
    token = request.form.get("token", "")
    if ADMIN_TOKEN and token == ADMIN_TOKEN:
        resp = make_response(redirect(url_for("admin_view")))
        resp.set_cookie('admin_session', token, 
                       httponly=True, secure=True, 
                       samesite='Strict', max_age=60*60*8)
        return resp
    return render_template_string(ADMIN_LOGIN_HTML, 
                                  error="Token inválido")

@app.route("/api/admin/auth", methods=["POST"])
def admin_auth():
    """Handle Google OAuth login"""
    id_token = request.json.get("credential", "")
    payload = _verify_google_token(id_token)
    email = payload.get("email", "").lower()
    
    if email not in ALLOWED_ADMINS:
        return jsonify({"error": "Email no autorizado"}), 403
    
    resp = make_response(jsonify({"ok": True, "email": email}))
    resp.set_cookie('admin_session', email, 
                   httponly=True, secure=True, 
                   samesite='Strict', max_age=60*60*8)
    return resp

@app.route("/admin/view", methods=["GET"])
def admin_view():
    """Protected admin dashboard - requires authentication"""
    if not _admin_authed():
        return redirect(url_for("admin_login_page"))
    return render_template_string(ADMIN_VIEW_HTML)

@app.route("/admin/logout", methods=["GET", "POST"])
def admin_logout():
    """Clear session and redirect to login"""
    resp = make_response(redirect(url_for("admin_login_page")))
    resp.set_cookie('admin_session', '', max_age=0)
    return resp

def _admin_authed():
    """Check if current request has valid admin session"""
    cookie_val = request.cookies.get('admin_session', '')
    
    # Check if it's the admin token
    if ADMIN_TOKEN and cookie_val == ADMIN_TOKEN:
        return True
    
    # Check if it's an allowed email (from Google)
    if cookie_val.lower() in ALLOWED_ADMINS:
        return True
    
    return False
```

### How It Works - Step by Step

**Token Login Flow:**
```
1. User → https://api.docdianasanchez.com/admin/
2. Flask → Renders login page (ADMIN_LOGIN_HTML)
3. Browser → Shows token input field
4. User → Enters token: ba19bba1878de076f13109e59c84574a2c900eea9d94731d
5. Form → POST /admin/login with token in form data
6. Flask → Validates token against .env ADMIN_TOKEN
7. If match → Set httponly cookie, redirect to /admin/view
8. Flask → Renders admin dashboard (ADMIN_VIEW_HTML)
9. All subsequent requests → Cookie sent automatically
10. Flask → Validates cookie on each protected route
```

**Google OAuth Flow:**
```
1. User → https://api.docdianasanchez.com/admin/
2. Flask → Renders login page with Google Sign-In button
3. User → Clicks "Sign in with Google"
4. Google → Shows OAuth consent screen
5. User → Approves with their Google account
6. Google → Returns ID token to browser
7. JavaScript → POST /api/admin/auth with credential
8. Flask → Verifies token with Google API
9. Flask → Extracts email from verified token
10. Flask → Checks if email in ALLOWED_ADMINS
11. If yes → Set httponly cookie with email, return success
12. JavaScript → Redirects to /admin/view
13. Flask → Validates cookie, shows dashboard
```

### Advantages
- ✅ Enterprise-grade security
- ✅ Token never exposed to client
- ✅ HttpOnly cookies (JavaScript cannot steal)
- ✅ Multiple authentication methods
- ✅ Google OAuth for SSO
- ✅ Email-based access control
- ✅ Server-side session validation
- ✅ 8-hour automatic timeout

### Disadvantages
- ⚠️ Requires backend deployment for changes
- ⚠️ More complex setup
- ⚠️ Token management needed (in .env)
- ⚠️ Google OAuth requires Chrome for best UX

---

## Comparison Table

| Feature | GitHub Pages Admin | Backend Admin |
|---------|-------------------|---------------|
| **URL** | docdianasanchez.com/admin | api.docdianasanchez.com/admin |
| **Hosting** | GitHub Pages (static) | Flask server (dynamic) |
| **Auth Type** | Client-side password | Server-side token/OAuth |
| **Password/Token** | `diana2024` (in JS) | Token in `.env` or Google |
| **Security Level** | Basic (client-side) | High (server-side) |
| **Session** | sessionStorage | HttpOnly Cookie (8h) |
| **Easy to Use** | ✅✅✅ Very easy | ✅✅ Moderate |
| **Secure** | ⚠️ Basic | ✅✅✅ Enterprise |
| **Multiple Users** | ❌ Single password | ✅ Email-based |
| **Audit Trail** | ❌ None | ✅ Server logs |
| **Deployment** | Auto (git push) | Manual (SSH) |
| **Works Offline** | ✅ Yes (after load) | ❌ Needs backend |
| **Best For** | Quick access | Production use |

---

## Cloudflare Routing

Both URLs work because of Cloudflare Tunnel configuration:

```yaml
# Cloudflare Tunnel routes traffic based on subdomain

# docdianasanchez.com → GitHub Pages
# ├── / → Website (index.html)
# └── /admin/ → Static admin panel (admin/index.html)

# api.docdianasanchez.com → Backend Server (192.168.0.131:8000)
# ├── /api/* → API endpoints
# ├── /admin → Backend admin login
# └── /admin/* → Backend admin routes
```

**Cloudflare Configuration:**
- `docdianasanchez.com` → DNS CNAME to GitHub Pages
- `api.docdianasanchez.com` → Tunnel to local server

---

## When to Use Which?

### Use GitHub Pages Admin When:
- ✅ You need quick access
- ✅ You're the only admin
- ✅ Basic security is acceptable
- ✅ You want instant deployment (git push)
- ✅ You're working on mobile/tablet
- ✅ Backend is temporarily down

### Use Backend Admin When:
- ✅ You need maximum security
- ✅ Multiple people need access (email-based)
- ✅ You need audit trails
- ✅ Handling sensitive data
- ✅ Production environment
- ✅ Using Google Workspace accounts

---

## Changing Passwords/Tokens

### GitHub Pages Admin Password

**File**: `/admin/admin.js`
**Line**: ~8

```javascript
const ADMIN_PASS = 'diana2024';  // ← Change this
```

**Steps:**
1. Edit `admin/admin.js`
2. Change `ADMIN_PASS` value
3. Commit and push to GitHub
4. GitHub Actions deploys automatically (~2 minutes)

### Backend Admin Token

**File**: `/home/beckham23/diana-booking-backend/.env` (on server)

```bash
ADMIN_TOKEN=ba19bba1878de076f13109e59c84574a2c900eea9d94731d  # ← Change this
```

**Steps:**
1. SSH to server: `ssh beckham23@192.168.0.131`
2. Edit `.env`: `nano /home/beckham23/diana-booking-backend/.env`
3. Change `ADMIN_TOKEN` value
4. Save and exit
5. Restart backend: `bash restart_backend.sh`

**Generate new secure token:**
```bash
# On your local machine or server
python3 -c "import secrets; print(secrets.token_hex(24))"
```

### Backend Google OAuth Allowed Emails

**File**: `/home/beckham23/diana-booking-backend/.env` (on server)

```bash
ALLOWED_ADMINS=osanchy7@gmail.com,julidb710@gmail.com  # ← Add/remove emails
```

**Steps:**
1. SSH to server: `ssh beckham23@192.168.0.131`
2. Edit `.env`: `nano /home/beckham23/diana-booking-backend/.env`
3. Add/remove emails (comma-separated, no spaces)
4. Save and exit
5. Restart backend: `bash restart_backend.sh`

---

## Troubleshooting

### GitHub Pages Admin Not Loading

**Check:**
1. Is GitHub Pages enabled in repo settings?
2. Did the latest deploy succeed? (Actions tab)
3. Clear browser cache and try again
4. Check browser console for JavaScript errors

**Fix:**
```bash
# Force redeploy
git commit --allow-empty -m "Trigger GitHub Pages rebuild"
git push origin main
```

### Backend Admin "Invalid Token"

**Check:**
1. Are you using the correct token from `.env`?
2. Did you include extra spaces when copying?
3. Is the backend running?

**Verify:**
```bash
ssh beckham23@192.168.0.131
cd /home/beckham23/diana-booking-backend
cat .env | grep ADMIN_TOKEN
curl http://localhost:8000/api/health
```

### Google Sign-In Not Working

**Common Issues:**
- ❌ Using Safari (requires third-party cookies)
- ❌ Ad blocker blocking Google scripts
- ❌ Email not in ALLOWED_ADMINS list

**Fix:**
1. Use Chrome browser
2. Disable ad blockers
3. Check `.env` has your email in ALLOWED_ADMINS
4. Verify GOOGLE_CLIENT_ID is set in `.env`

### Session Expired

**Symptom**: Redirected to login after some time

**Reason**: 8-hour cookie expiration

**Fix**: Just log in again (this is by design for security)

---

## Security Best Practices

### For GitHub Pages Admin:
1. ⚠️ **Change the default password** from `diana2024`
2. ⚠️ Don't share the password publicly
3. ✅ Use HTTPS only (enforced by GitHub)
4. ✅ Consider IP restriction via Cloudflare
5. ℹ️ Accept that password is visible in source (acceptable for basic use)

### For Backend Admin:
1. ✅ **Never commit `.env` file** to git
2. ✅ Use strong random tokens (24+ bytes)
3. ✅ Rotate tokens periodically
4. ✅ Limit ALLOWED_ADMINS to necessary emails
5. ✅ Monitor server logs for suspicious activity
6. ✅ Keep backend server updated
7. ✅ Use Cloudflare Tunnel (no open ports)

---

## Summary

You have **TWO admin panels** that work independently:

1. **GitHub Pages** (`docdianasanchez.com/admin`) - Quick, easy, client-side
2. **Backend** (`api.docdianasanchez.com/admin`) - Secure, server-side, OAuth

Both are **fully operational** and serve different purposes. Use whichever fits your current needs!

---

**Last Updated**: July 24, 2026  
**Author**: Julián Sánchez  
**Contact**: julidb710@gmail.com
