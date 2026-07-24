# Admin Systems - Quick Reference

## 🚀 Quick Access

### Option 1: GitHub Pages (Easy & Fast)
**URL**: `https://docdianasanchez.com/admin/`  
**Password**: `diana2024`  
**How**: Enter password → Click "Entrar"

### Option 2: Backend (Secure)
**URL**: `https://api.docdianasanchez.com/admin/`  
**Token**: `ba19bba1878de076f13109e59c84574a2c900eea9d94731d`  
**OR**: Click "Sign in with Google" (Chrome only)

---

## 🔑 Credentials Reference

| System | Type | Value | Location |
|--------|------|-------|----------|
| GitHub Pages | Password | `diana2024` | In `/admin/admin.js` |
| Backend | Token | `ba19bba187...` | In server `.env` |
| Backend | Google | Allowed emails | In server `.env` |

---

## 📂 File Locations

### GitHub Pages Admin
```
/admin/
├── index.html          # Main page
├── admin.css           # Styles
├── admin.js            # Logic (has password)
├── medical-records.html
└── medical-records.js
```

### Backend Admin
```
/home/beckham23/diana-booking-backend/
├── app.py              # Flask app (has routes)
├── .env                # Secrets (token, emails)
└── restart_backend.sh  # Restart script
```

---

## 🔧 Common Tasks

### Change GitHub Password
```bash
# Edit line ~8 in admin/admin.js
const ADMIN_PASS = 'NEW_PASSWORD_HERE';

# Commit and push
git add admin/admin.js
git commit -m "chore: Update admin password"
git push origin main
```

### Change Backend Token
```bash
# SSH to server
ssh beckham23@192.168.0.131

# Generate new token
python3 -c "import secrets; print(secrets.token_hex(24))"

# Edit .env
nano /home/beckham23/diana-booking-backend/.env
# Update ADMIN_TOKEN=<new_token>

# Restart
bash /home/beckham23/diana-booking-backend/restart_backend.sh
```

### Add Google Admin Email
```bash
# SSH to server
ssh beckham23@192.168.0.131

# Edit .env
nano /home/beckham23/diana-booking-backend/.env
# Update ALLOWED_ADMINS=email1@gmail.com,email2@gmail.com

# Restart
bash /home/beckham23/diana-booking-backend/restart_backend.sh
```

### Restart Backend
```bash
ssh beckham23@192.168.0.131 \
  "cd /home/beckham23/diana-booking-backend && bash restart_backend.sh"
```

---

## 🐛 Troubleshooting

### "Invalid password" (GitHub Pages)
- Check you're using: `diana2024`
- Clear browser cache
- Check browser console for errors

### "Invalid token" (Backend)
- Check token has no extra spaces
- Verify token matches `.env` on server
- Try Google Sign-In instead

### "Email not authorized" (Google)
- Your email must be in `ALLOWED_ADMINS` in `.env`
- SSH to server and add your email
- Restart backend

### Backend not responding
```bash
# Check if backend is running
ssh beckham23@192.168.0.131 \
  "curl -s http://localhost:8000/api/health"

# Should return: {"status":"ok","db":"up"}

# If not, restart:
ssh beckham23@192.168.0.131 \
  "cd /home/beckham23/diana-booking-backend && bash restart_backend.sh"
```

---

## 📊 Database Stats

- **Total Appointments**: 283
  - Real: 83
  - Dummy (for testing): 200
- **Status Distribution**:
  - Pending: ~40%
  - Confirmed: ~40%
  - Cancelled: ~10%
  - Completed: ~10%

---

## 🔗 Useful URLs

| Purpose | URL |
|---------|-----|
| Main website | https://docdianasanchez.com |
| GitHub Pages Admin | https://docdianasanchez.com/admin/ |
| Backend Admin | https://api.docdianasanchez.com/admin/ |
| API Health | https://api.docdianasanchez.com/api/health |
| GitHub Repo | https://github.com/sancho16/docDianaSanchez |

---

## 📞 Support

**Developer**: Julián Sánchez  
**Email**: julidb710@gmail.com  
**GitHub**: [@sancho16](https://github.com/sancho16)

---

**Quick Tip**: For daily use, bookmark **GitHub Pages admin** (`docdianasanchez.com/admin`) - it's faster and easier!
