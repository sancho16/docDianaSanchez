# Admin Panel - Technical Documentation

## Overview
The admin panel for **docdianasanchez.com** is a bilingual (EN/ES) dark-themed dashboard for managing appointment bookings. It features modern Apple-style glassmorphism design, real-time charts, and Safari-compatible authentication.

---

## 🌐 Access URLs

- **Login**: https://api.docdianasanchez.com/admin
- **Dashboard**: https://api.docdianasanchez.com/admin/view
- **API Endpoints**:
  - `POST /api/bookings` - Submit new booking
  - `GET /api/admin/bookings` - List all bookings (auth required)
  - `GET /api/admin/stats` - Dashboard statistics (auth required)
  - `PATCH /api/admin/bookings/:id` - Update booking status (auth required)

---

## 🔐 Authentication

### Option 1: Admin Token (Recommended - Works in ALL browsers including Safari)
**Token**: `ba19bba1878de076f13109e59c84574a2c900eea9d94731d`

Steps:
1. Go to https://api.docdianasanchez.com/admin
2. Enter token in password field
3. Click "Sign in" / "Iniciar sesión"

### Option 2: Google Sign-In (Chrome only)
**Allowed Admins**:
- osanchy7@gmail.com
- julidb710@gmail.com

**Why Safari doesn't work**: Safari blocks third-party cookies by default (privacy feature), which breaks Google's authentication widget. This is browser behavior, not a bug.

---

## 🌍 Bilingual Support

The admin panel supports **English** and **Spanish** with a language toggle in the top-right corner.

- **Default**: English (EN)
- **Language persistence**: Saved in browser localStorage
- **Prefix convention**: All Spanish text uses the language toggle, no hardcoded prefixes

### Translation Coverage:
- Login page: titles, buttons, form labels, error messages
- Dashboard: headers, KPI labels, chart labels, table headers, action buttons
- All UI elements respond to language switch in real-time

---

## 🎨 Dark Theme Design

### Color Palette:
```css
--bg-gradient-start: #001f25  /* Deep teal */
--bg-gradient-end: #003d47    /* Medium teal */
--glass-bg: rgba(255,255,255,0.08)  /* Glassmorphism */
--glass-border: rgba(255,255,255,0.12)
--text-primary: #ffffff
--text-secondary: rgba(255,255,255,0.7)
--text-muted: rgba(255,255,255,0.5)
--accent: #5fe3d6  /* Teal accent */
--accent-hover: #00b8a3
```

### Design Features:
- **Glassmorphism**: `backdrop-filter: blur(24px) saturate(180%)`
- **Gradient backgrounds**: Linear gradients from dark to medium teal
- **Smooth animations**: Fade-in on load, hover effects on cards
- **Responsive grid**: Auto-fit columns for KPIs, 2-column charts on desktop
- **Mobile-first**: Collapses to single column on tablets/phones

---

## 📊 Dashboard Features

### KPI Cards (4 metrics):
1. **Real appointments (total)** - Count of non-dummy bookings
2. **Pending** - Bookings with `status = 'pending'`
3. **Last 7 days** - Bookings created in past week
4. **Dummy (practice)** - Test bookings for development

### Charts (Chart.js v4.4.1):
1. **Line chart** - Appointments per day (last 90 days)
2. **Doughnut chart** - Bookings by status (pending/confirmed/completed/cancelled)
3. **Bar chart** - Bookings by service type
4. **Pie chart** - Real vs. Dummy bookings

### Data Table:
- Columns: ID, Name, Phone, Email, Date, Time, Service, Message, Status, Action
- **Filters**: All/Dummy only, Status (pending/confirmed/completed/cancelled)
- **Actions**: Change status via dropdown (Confirm/Complete/Cancel)
- **CSV Export**: Download filtered bookings as CSV

---

## 🖥️ Server Configuration

### Backend Server
**Location**: beckham23@192.168.0.131  
**Path**: `~/diana-booking-backend/`  
**Process**: `gunicorn -w 2 -b 127.0.0.1:8000 app:app`  
**Logs**: `~/diana-booking-backend/gunicorn.log`

### Database
**Type**: PostgreSQL  
**Name**: `diana_bookings`  
**User**: `diana_app`  
**Connection**: `postgresql://diana_app:diana_228d35464ad83ba0e3e3@127.0.0.1/diana_bookings`

### Environment Variables (.env)
```bash
DATABASE_URL=postgresql://diana_app:diana_228d35464ad83ba0e3e3@127.0.0.1/diana_bookings
ADMIN_TOKEN=ba19bba1878de076f13109e59c84574a2c900eea9d94731d
GOOGLE_CLIENT_ID=892965153332-amv5b3n7nj303bjsclsu35fjcm2pretm.apps.googleusercontent.com
ALLOWED_ADMINS=osanchy7@gmail.com,julidb710@gmail.com
ALLOWED_ORIGINS=https://docdianasanchez.com,https://www.docdianasanchez.com
```

### Cloudflare Tunnel
**Domain**: `api.docdianasanchez.com`  
**Target**: `http://127.0.0.1:8000` (local gunicorn)  
**SSL**: Managed by Cloudflare

---

## 🔄 Server Management Commands

### Restart Backend
```bash
ssh beckham23@192.168.0.131
cd ~/diana-booking-backend
pkill -f 'gunicorn.*app:app'
gunicorn -w 2 -b 127.0.0.1:8000 app:app > gunicorn.log 2>&1 &
```

### Check Server Status
```bash
ps aux | grep gunicorn | grep -v grep
```

### View Logs
```bash
tail -f ~/diana-booking-backend/gunicorn.log
```

### Check Database Connection
```bash
psql -U diana_app -d diana_bookings -c "SELECT count(*) FROM bookings;"
```

---

## 🚀 Deployment Workflow

### Frontend (GitHub Pages)
1. **Branch structure**:
   - `DevTurquoiseThemed` - Active development (teal theme)
   - `DevRedThemed` - Alternative theme branch
   - `Prod` - Production branch (deployed to GitHub Pages)

2. **Deploy process**:
```bash
cd /Users/juliansanchez/docDianaSanchez
git checkout DevTurquoiseThemed
git pull origin DevTurquoiseThemed

# Make changes, test locally

git add .
git commit -m "Description of changes"
git push origin DevTurquoiseThemed

# When ready for production:
git checkout Prod
git merge DevTurquoiseThemed -m "Merge DevTurquoiseThemed to Prod"
git push origin Prod
```

3. **GitHub Pages settings**:
   - Source: `Prod` branch
   - Domain: `docdianasanchez.com`
   - CNAME configured

### Backend (Server @ 192.168.0.131)
1. **Update app.py** with new HTML templates or Python code
2. **Restart gunicorn** (see Server Management Commands above)
3. **No git tracking** - Backend is manually deployed on server

---

## 🐛 Troubleshooting

### Google Sign-In Not Showing
**Symptom**: Button doesn't render  
**Causes**:
- `GOOGLE_CLIENT_ID` not set in `.env`
- Google script blocked by browser extension
- Third-party cookies disabled (Safari)

**Fix**:
- Hard refresh: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
- Check browser console for errors
- Use token login instead

### Charts Not Rendering
**Symptom**: Empty panels where charts should be  
**Causes**:
- Chart.js script didn't load (CDN issue)
- Canvas height not set properly
- API returning empty data

**Fix**:
- Check browser console for Chart.js errors
- Verify `/api/admin/stats` returns valid JSON
- Ensure canvas has explicit height in CSS

### Token Login Fails
**Symptom**: "Invalid token" error  
**Causes**:
- Token mismatch with `.env` file
- Server not reading `.env` properly
- Cookie not being set

**Fix**:
```bash
ssh beckham23@192.168.0.131
cd ~/diana-booking-backend
cat .env | grep ADMIN_TOKEN
# Should show: ADMIN_TOKEN=ba19bba1878de076f13109e59c84574a2c900eea9d94731d
```

### Database Connection Errors
**Symptom**: 503 errors, `/api/health` fails  
**Causes**:
- PostgreSQL service down
- Wrong connection string
- Network firewall blocking port 5432

**Fix**:
```bash
sudo systemctl status postgresql
sudo systemctl restart postgresql
psql -U diana_app -d diana_bookings -c "SELECT 1;"
```

---

## 📝 Recent Changes (2026-07-22)

### ✅ Completed
1. **Bilingual support** - EN/ES toggle with localStorage persistence
2. **Dark theme redesign** - Apple-style glassmorphism, teal gradients
3. **Safari compatibility warning** - Auto-detects Safari, shows token login first
4. **Fixed chart rendering** - Proper canvas sizing, responsive:true, maintainAspectRatio:false
5. **Improved UX** - Larger KPI cards, better spacing, hover effects
6. **Production deployment** - Merged DevTurquoiseThemed → Prod, pushed to GitHub Pages

### 🔧 Technical Improvements
- Chart instances properly destroyed before re-render
- Language-specific chart labels (Real/Reales, appointments/citas)
- CSS custom properties for easy theme customization
- Explicit canvas height: `300px` to prevent layout shift

---

## 📚 Code Structure

### Backend (app.py)
```
diana-booking-backend/
├── app.py                  # Flask application
├── notify.py               # Email notifications
├── .env                    # Environment variables
├── requirements.txt        # Python dependencies
└── gunicorn.log           # Server logs
```

### Frontend (GitHub repo)
```
docDianaSanchez/
├── index.html             # Landing page
├── success.html           # Form submission success page
├── css/
│   ├── style.css         # Base styles
│   ├── updates.css       # Additional styles
│   └── theme-turquoise.css  # Teal theme
├── js/
│   └── main.js           # Frontend JavaScript
├── assets/               # Images, favicons
└── CNAME                 # GitHub Pages domain config
```

**Note**: Admin panel HTML is **embedded in app.py**, not separate files.

---

## 🔒 Security Notes

1. **Admin token** should be rotated periodically
2. **CORS** restricted to `docdianasanchez.com` and `www.docdianasanchez.com`
3. **Rate limiting** on booking API (15 requests per 20 minutes per IP)
4. **Honeypot field** (`_gotcha`) catches bots
5. **Input validation** on all form fields (regex patterns, length checks)
6. **SQL injection protection** via parameterized queries (psycopg2)
7. **HTTPS only** - Cloudflare manages SSL certificates

---

## 📞 Contact & Support

**Developer**: Julian Sanchez  
**Admin emails**: osanchy7@gmail.com, julidb710@gmail.com  
**Domain**: docdianasanchez.com  
**Server**: beckham23@192.168.0.131 (local network)

---

*Last updated: July 22, 2026*
