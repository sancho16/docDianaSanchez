# Admin Panel Migration to Backend Server

## 📋 Overview

Migrating the admin panel from GitHub Pages static hosting to the backend Flask server to enable proper server-side authentication, session management, and dynamic content serving.

---

## 🎯 Goals

1. **Server-Side Authentication**: Move from client-side token checking to server-side session authentication
2. **Separate Login Flow**: Login page → authenticate → redirect to admin view
3. **Unified Hosting**: Both frontend and backend admin served from same domain (docdianasanchez.com)
4. **Protected Routes**: Admin view only accessible when authenticated

---

## 🏗️ New Architecture

### **Before (GitHub Pages)**
```
https://docdianasanchez.com/admin/
  ↓
Static index.html with login + admin in one file
  ↓
Client-side JS checks token
  ↓
Shows/hides login screen vs admin panel
```

### **After (Backend Server)**
```
https://docdianasanchez.com/admin/
  ↓
Backend serves login.html
  ↓
POST /admin/login (authenticate)
  ↓
Set session cookie → Redirect to /admin/view
  ↓
Backend serves admin-view.html (protected route)
```

---

## 📂 File Structure

### **Local Development**
```
/Users/juliansanchez/docDianaSanchez/
├── admin/
│   ├── login.html           # NEW: Separate login page
│   ├── admin-view.html      # NEW: Separate admin panel
│   ├── admin.css            # Shared styles
│   └── admin.js             # Updated auth logic
```

### **Backend Server**
```
/home/beckham23/diana-booking-backend/
├── app.py                   # Updated routes
├── templates/
│   ├── login.html           # Served at /admin/
│   ├── admin-view.html      # Served at /admin/view
│   ├── admin.css            # Loaded by both pages
│   └── admin.js             # Client-side logic
```

---

## 🔐 Authentication Flow

### **1. Login Page** (`/admin/`)
- **URL**: https://docdianasanchez.com/admin/
- **File**: `templates/login.html`
- **Route**: 
  ```python
  @app.route("/admin/", methods=["GET"])
  def admin_login_page():
      if _admin_authed():
          return redirect(url_for("admin_view"))
      return render_template("login.html")
  ```
- **What it does**: Shows login form, redirects if already logged in

### **2. Login Submit** (`POST /admin/login`)
- **URL**: https://docdianasanchez.com/admin/login
- **Route**:
  ```python
  @app.route("/admin/login", methods=["POST"])
  def admin_login():
      password = request.form.get("password")
      if password == ADMIN_TOKEN:
          resp = make_response(redirect(url_for("admin_view")))
          resp.set_cookie(ADMIN_COOKIE, "authenticated", 
                         httponly=True, secure=True, 
                         samesite="Strict", max_age=28800)  # 8 hours
          return resp
      return render_template("login.html", error="Contraseña incorrecta")
  ```
- **What it does**: Validates password, sets secure cookie, redirects to admin view

### **3. Admin View** (`/admin/view`)
- **URL**: https://docdianasanchez.com/admin/view
- **File**: `templates/admin-view.html`
- **Route**:
  ```python
  @app.route("/admin/view", methods=["GET"])
  def admin_view():
      if not _admin_authed():
          return redirect(url_for("admin_login_page"))
      return render_template("admin-view.html")
  ```
- **What it does**: Protected route, shows admin panel if authenticated

### **4. Logout** (`/admin/logout`)
- **URL**: https://docdianasanchez.com/admin/logout
- **Route**:
  ```python
  @app.route("/admin/logout", methods=["GET", "POST"])
  def admin_logout():
      resp = make_response(redirect(url_for("admin_login_page")))
      resp.delete_cookie(ADMIN_COOKIE)
      return resp
  ```
- **What it does**: Clears session cookie, redirects to login

---

## 🔄 Changes Required

### **1. Split index.html**

**Current**: Single `index.html` with both login and admin
```html
<div class="adm-login" id="adm-login"><!-- login form --></div>
<div class="adm-app" id="adm-app" hidden><!-- admin panel --></div>
```

**New**: Two separate files

**login.html**:
```html
<!DOCTYPE html>
<html lang="es">
<head><!-- head content --></head>
<body>
  <div class="adm-login">
    <div class="adm-login__card">
      <h1>Panel de administración</h1>
      <form method="POST" action="/admin/login">
        <input type="password" name="password" required />
        <button type="submit">Entrar</button>
      </form>
    </div>
  </div>
</body>
</html>
```

**admin-view.html**:
```html
<!DOCTYPE html>
<html lang="es">
<head><!-- head content --></head>
<body>
  <div class="adm-app">
    <!-- sidebar, tabs, content -->
  </div>
  <script src="/templates/admin.js"></script>
</body>
</html>
```

### **2. Update app.py Routes**

Replace embedded HTML strings with `render_template()`:

```python
# Remove ADMIN_LOGIN_HTML and ADMIN_VIEW_HTML strings

@app.route("/admin/", methods=["GET"])
def admin_login_page():
    if _admin_authed():
        return redirect(url_for("admin_view"))
    return render_template("login.html")

@app.route("/admin/login", methods=["POST"])
def admin_login():
    password = request.form.get("password", "")
    if password == ADMIN_TOKEN:
        resp = make_response(redirect(url_for("admin_view")))
        resp.set_cookie(ADMIN_COOKIE, "authenticated", 
                       httponly=True, secure=True, 
                       samesite="Strict", max_age=28800)
        return resp
    return render_template("login.html", error="Contraseña incorrecta")

@app.route("/admin/view", methods=["GET"])
def admin_view():
    if not _admin_authed():
        return redirect(url_for("admin_login_page"))
    return render_template("admin-view.html")

@app.route("/admin/logout", methods=["GET", "POST"])
def admin_logout():
    resp = make_response(redirect(url_for("admin_login_page")))
    resp.delete_cookie(ADMIN_COOKIE)
    return resp

# Serve static files (CSS, JS)
@app.route("/templates/<path:filename>")
def serve_template_assets(filename):
    return send_from_directory("templates", filename)
```

### **3. Update admin.js**

Remove client-side authentication logic:

**Before**:
```javascript
// Client-side token check
const loginForm = document.getElementById('login-form');
loginForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const password = document.getElementById('adm-pass').value;
  if (password === 'diana2024') {
    document.cookie = 'admin_token=...';
    showApp();
  }
});
```

**After**:
```javascript
// Server handles login via form POST
// Just focus on loading data when page loads

document.addEventListener('DOMContentLoaded', () => {
  // We're already authenticated (server checked)
  loadBookings();
  loadAppointments();
  loadReviews();
});
```

---

## 🚀 Deployment Steps

### **Step 1: Prepare Local Files**
```bash
cd /Users/juliansanchez/docDianaSanchez/admin/
# Split index.html into login.html and admin-view.html
# Update admin.js (remove client-side auth)
```

### **Step 2: Create templates/ Directory on Server**
```bash
ssh beckham23@192.168.0.131 "mkdir -p /home/beckham23/diana-booking-backend/templates"
```

### **Step 3: Upload Files**
```bash
scp admin/login.html beckham23@192.168.0.131:/home/beckham23/diana-booking-backend/templates/
scp admin/admin-view.html beckham23@192.168.0.131:/home/beckham23/diana-booking-backend/templates/
scp admin/admin.css beckham23@192.168.0.131:/home/beckham23/diana-booking-backend/templates/
scp admin/admin.js beckham23@192.168.0.131:/home/beckham23/diana-booking-backend/templates/
```

### **Step 4: Update app.py**
```bash
scp backend/app.py beckham23@192.168.0.131:/home/beckham23/diana-booking-backend/app.py
```

### **Step 5: Restart Backend**
```bash
ssh beckham23@192.168.0.131 "cd /home/beckham23/diana-booking-backend && bash restart_backend.sh"
```

---

## ✅ Testing Checklist

- [ ] Navigate to https://docdianasanchez.com/admin/ → See login page
- [ ] Enter wrong password → See error message
- [ ] Enter correct password → Redirect to /admin/view
- [ ] Refresh /admin/view → Stay logged in (cookie persists)
- [ ] Try accessing /admin/view directly without login → Redirect to /admin/
- [ ] Click logout → Redirect to /admin/ and clear session
- [ ] Verify bookings load correctly in admin view
- [ ] Verify appointments tab shows data
- [ ] Verify search functionality works
- [ ] Verify medical records can be saved
- [ ] Test on mobile device (responsive design)

---

## 🔒 Security Considerations

### **Session Cookie**
- `httponly=True`: JavaScript cannot access cookie (XSS protection)
- `secure=True`: Cookie only sent over HTTPS
- `samesite="Strict"`: CSRF protection
- `max_age=28800`: 8-hour session timeout

### **Password Storage**
- Admin password stored in environment variable `ADMIN_TOKEN`
- Never committed to git (in .env file, listed in .gitignore)

### **Protected Routes**
- All admin routes check `_admin_authed()` before serving
- Unauthenticated requests redirect to login page

---

## 🌐 URL Mapping

| URL | Purpose | Authentication |
|-----|---------|---------------|
| `https://docdianasanchez.com/admin/` | Login page | Public |
| `https://docdianasanchez.com/admin/login` | Login POST handler | Public |
| `https://docdianasanchez.com/admin/view` | Admin panel | Protected |
| `https://docdianasanchez.com/admin/logout` | Logout | Protected |
| `https://api.docdianasanchez.com/api/bookings` | Bookings API | Public |
| `https://api.docdianasanchez.com/api/admin/*` | Admin APIs | Protected (cookie) |

---

## 🔧 Rollback Plan

If migration fails, revert to old system:

```bash
ssh beckham23@192.168.0.131 "cd /home/beckham23/diana-booking-backend && git checkout app.py && bash restart_backend.sh"
```

Old URLs will still work:
- `https://api.docdianasanchez.com/admin/` (old backend login)
- `https://api.docdianasanchez.com/admin/view` (old backend admin)

---

## 📝 Notes

- **GitHub Pages version** at `https://docdianasanchez.com/admin/` will be replaced with backend-served version
- **Old backend version** at `https://api.docdianasanchez.com/admin/` can be deprecated after migration
- **Database and API endpoints** remain unchanged
- **All existing bookings and data** are preserved

---

## 🎉 Benefits After Migration

1. ✅ **True Server-Side Authentication**: Secure session management
2. ✅ **Instant Updates**: No waiting for GitHub Pages rebuild
3. ✅ **Single Deployment**: Update backend + admin in one go
4. ✅ **Better Security**: HttpOnly cookies, CSRF protection
5. ✅ **Easier Maintenance**: All code in one repository on server
6. ✅ **No CSS/JS Caching Issues**: Server controls cache headers

---

## 📞 Support

- **Backend Server**: `beckham23@192.168.0.131:/home/beckham23/diana-booking-backend/`
- **Local Development**: `/Users/juliansanchez/docDianaSanchez/`
- **Admin Password**: Stored in `.env` file as `ADMIN_TOKEN`
- **Restart Backend**: `ssh beckham23@192.168.0.131 "cd /home/beckham23/diana-booking-backend && bash restart_backend.sh"`

---

*Migration Date: July 24, 2026*  
*Author: Julian Sanchez*
