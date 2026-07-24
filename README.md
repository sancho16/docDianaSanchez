# Dr. Diana Carolina Sánchez Dávila - Medical Services Website

Bilingual medical services booking platform with dual admin panel system.

## 🌐 Live URLs

- **Main Website**: https://docdianasanchez.com
- **Admin Panel (GitHub)**: https://docdianasanchez.com/admin/
- **Admin Panel (Backend)**: https://api.docdianasanchez.com/admin/
- **API Base**: https://api.docdianasanchez.com

## 📚 Documentation

### Admin Systems
- **[Admin Systems Architecture](docs/ADMIN_SYSTEMS_ARCHITECTURE.md)** - Complete guide to both admin panels
- **[Admin Quick Reference](docs/ADMIN_QUICK_REFERENCE.md)** - Quick access guide and credentials
- **[Full Stack Architecture](docs/Full-Stack-Architecture-Documentation.md)** - Overall system design
- **[Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** - How to deploy changes

### Recent Updates
- **[Backend Restored](BACKEND_RESTORED.md)** - Latest system status (July 24, 2026)
- **[Admin Fix Complete](ADMIN_FIX_COMPLETE.md)** - Admin authentication fixes

## 🏗️ Architecture Overview

### Frontend (GitHub Pages)
- **Static website** with booking form
- **Client-side admin panel** with password authentication
- **Automatic deployment** via GitHub Actions

### Backend (Flask Server)
- **Python Flask API** on private server (192.168.0.131)
- **PostgreSQL database** with 283 appointments
- **Server-side admin panel** with token/OAuth authentication
- **Cloudflare Tunnel** for secure public access

### Admin Panels (Dual System)

#### 1. GitHub Pages Admin
- **URL**: https://docdianasanchez.com/admin/
- **Auth**: Client-side password (`diana2024`)
- **Use case**: Quick access, daily operations
- **Pros**: Fast, easy, auto-deploys
- **Files**: `/admin/` directory

#### 2. Backend Admin
- **URL**: https://api.docdianasanchez.com/admin/
- **Auth**: Server-side token OR Google OAuth
- **Use case**: Secure operations, multiple users
- **Pros**: Enterprise security, audit trails
- **Token**: In `.env` on server

## 🚀 Quick Start

### For Users
1. Visit https://docdianasanchez.com
2. Fill out booking form
3. Receive confirmation email

### For Admins (GitHub Pages)
1. Visit https://docdianasanchez.com/admin/
2. Enter password: `diana2024`
3. Manage bookings and reviews

### For Admins (Backend)
1. Visit https://api.docdianasanchez.com/admin/
2. Option A: Enter admin token
3. Option B: Sign in with Google (Chrome)
4. Access secure admin dashboard

## 🛠️ Tech Stack

### Frontend
- HTML5, CSS3, JavaScript (vanilla)
- GitHub Pages hosting
- Cloudflare CDN & DNS

### Backend
- Python 3.x
- Flask web framework
- PostgreSQL database
- Gunicorn WSGI server
- Cloudflare Tunnel

### Mobile
- SwiftUI (iOS 18)
- CoreLocation
- Native iOS app (in `/ios/` directory)

### Infrastructure
- **Hosting**: GitHub Pages (frontend), Private server (backend)
- **DNS**: Cloudflare
- **Tunnel**: Cloudflare Tunnel (no port forwarding)
- **Email**: Gmail SMTP
- **Auth**: Password, Token, Google OAuth 2.0

## 📁 Project Structure

```
docDianaSanchez/
├── admin/                      # GitHub Pages admin panel
│   ├── index.html              # Admin login & dashboard
│   ├── admin.js                # Client-side logic (has password)
│   ├── admin.css               # Styles
│   └── medical-records.*       # Medical records pages
├── backend/                    # Flask backend server
│   ├── app.py                  # Main Flask application
│   ├── .env                    # Environment variables (NOT in git)
│   ├── requirements.txt        # Python dependencies
│   ├── restart_backend.sh      # Backend restart script
│   └── generate_dummy_appointments.py  # Test data generator
├── docs/                       # Documentation
│   ├── ADMIN_SYSTEMS_ARCHITECTURE.md   # Admin panels guide
│   ├── ADMIN_QUICK_REFERENCE.md        # Quick reference
│   └── Full-Stack-Architecture-Documentation.md
├── ios/                        # iOS Swift app
├── css/                        # Website styles
├── js/                         # Website JavaScript
├── assets/                     # Images, favicons
├── index.html                  # Main website
├── review.html                 # Review submission page
└── README.md                   # This file
```

## 🔐 Credentials & Access

### GitHub Pages Admin
- **Password**: `diana2024`
- **Location**: `/admin/admin.js` line 8
- **To change**: Edit admin.js, commit, push

### Backend Admin Token
- **Token**: In `.env` file on server
- **Location**: `/home/beckham23/diana-booking-backend/.env`
- **To change**: SSH to server, edit .env, restart

### Backend Google OAuth
- **Allowed Emails**: In `.env` file (`ALLOWED_ADMINS`)
- **To add**: SSH to server, edit .env, restart

**See [Admin Quick Reference](docs/ADMIN_QUICK_REFERENCE.md) for detailed instructions.**

## 🔧 Development

### Local Backend Setup
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your credentials

# Run development server
python app.py
```

### Deploy Frontend Changes
```bash
# Make changes to HTML/CSS/JS
git add .
git commit -m "Your changes"
git push origin main

# GitHub Actions automatically deploys to GitHub Pages
```

### Deploy Backend Changes
```bash
# Copy files to server
scp backend/app.py beckham23@192.168.0.131:/home/beckham23/diana-booking-backend/

# Restart backend
ssh beckham23@192.168.0.131 \
  "cd /home/beckham23/diana-booking-backend && bash restart_backend.sh"
```

## 📊 Database

### PostgreSQL
- **Host**: 127.0.0.1 (localhost on server)
- **Database**: diana_bookings
- **User**: diana_app
- **Connection**: Via DATABASE_URL in .env

### Current Data
- **Total Appointments**: 283
  - Real: 83
  - Dummy (testing): 200
- **Status Distribution**: 40% pending, 40% confirmed, 10% cancelled, 10% completed
- **Date Range**: Last 6 months to next 3 months

## 🧪 Testing

### Test Email Notifications
```bash
ssh beckham23@192.168.0.131 \
  "cd /home/beckham23/diana-booking-backend && python3 test_email_now.py"
```

### Generate Test Appointments
```bash
ssh beckham23@192.168.0.131 \
  "cd /home/beckham23/diana-booking-backend && python3 generate_dummy_appointments.py"
```

### Check Backend Health
```bash
curl https://api.docdianasanchez.com/api/health
# Should return: {"status":"ok","db":"up"}
```

## 🐛 Troubleshooting

### Backend Not Responding
```bash
# Check status
ssh beckham23@192.168.0.131 "curl http://localhost:8000/api/health"

# Restart if needed
ssh beckham23@192.168.0.131 \
  "cd /home/beckham23/diana-booking-backend && bash restart_backend.sh"
```

### GitHub Pages Not Updating
- Check GitHub Actions tab for deployment status
- Clear browser cache
- Wait 2-3 minutes for CDN propagation

### Admin Login Not Working
- **GitHub Pages**: Verify password is `diana2024`
- **Backend**: Check token in `.env` matches what you're entering
- **Google**: Ensure your email is in `ALLOWED_ADMINS`

**See [Admin Systems Architecture](docs/ADMIN_SYSTEMS_ARCHITECTURE.md) for detailed troubleshooting.**

## 🔒 Security

### Best Practices Implemented
- ✅ HTTPS only (enforced)
- ✅ HttpOnly cookies (XSS protection)
- ✅ Secure cookies (HTTPS only)
- ✅ SameSite cookies (CSRF protection)
- ✅ Cloudflare Tunnel (no open ports)
- ✅ Environment variables for secrets
- ✅ .env file not committed to git
- ✅ 8-hour session timeout

### Recommendations
- 🔄 Rotate admin tokens regularly
- 🔄 Review ALLOWED_ADMINS list periodically
- 🔄 Monitor server logs for suspicious activity
- 🔄 Keep dependencies updated
- 🔄 Set up automated database backups

## 📞 Support

**Developer**: Julián Sánchez  
**Role**: Full Stack Developer | Scrum Master Certified | UiPath Advanced RPA Developer  
**Email**: julidb710@gmail.com  
**GitHub**: [@sancho16](https://github.com/sancho16)

**For Dr. Diana Carolina Sánchez Dávila**  
Medical Services - Costa Rica  
https://docdianasanchez.com

## 📄 License

Private project - All rights reserved

---

**Last Updated**: July 24, 2026  
**Version**: 2.0  
**Status**: ✅ Production
