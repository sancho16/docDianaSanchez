# Dr. Diana Sánchez Website - Full Stack Architecture Documentation

## 📋 Executive Summary

This document provides a comprehensive overview of the full-stack architecture for Dr. Diana Sánchez's medical consultation website, including all dependencies, infrastructure components, and deployment configurations.

**Website URL:** https://docdianasanchez.com  
**Admin Panel:** https://api.docdianasanchez.com/admin  
**API Endpoint:** https://api.docdianasanchez.com/api/bookings

---

## 🏗️ Architecture Overview

The system follows a modern full-stack architecture with the following components:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend       │    │    Database     │
│   (Static)      │◄──►│   (Home Server)  │◄──►│   PostgreSQL    │
│  GitHub Pages   │    │  192.168.0.131   │    │    Local DB     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │
         │                        │
         ▼                        ▼
┌─────────────────┐    ┌──────────────────┐
│   Cloudflare    │    │      SMTP        │
│      CDN        │    │   Gmail Service  │
│   (Tunneling)   │    │  (Notifications) │
└─────────────────┘    └──────────────────┘
```

---

## 🖥️ Frontend Architecture

### Technology Stack
- **HTML5** - Semantic markup with accessibility features
- **CSS3** - Modern styling with glassmorphism design
- **Vanilla JavaScript** - No frameworks, pure JS
- **i18n System** - Bilingual support (English/Spanish)

### Key Components

#### 1. Static Assets
```
docDianaSanchez/
├── assets/
│   ├── diana.jpg           # Profile photo
│   ├── robot.png           # Email footer asset
│   ├── favicon.svg         # Site icon
│   └── og-image.svg        # Social media preview
├── css/
│   ├── style.css           # Base styles
│   ├── theme-turquoise.css # Color theme
│   └── updates.css         # Latest updates
├── js/
│   ├── main.js             # Core functionality
│   └── i18n.js             # Translation system
└── index.html              # Main page
```

#### 2. Features Implemented
- **Bilingual Support** - Real-time language switching
- **Responsive Design** - Mobile-first approach
- **Modern Date/Time Picker** - Haptic feedback enabled
- **Form Validation** - Client-side validation
- **Service Cards** - Flip animations and hover effects
- **LinkedIn Integration** - Professional profile link

### Deployment
- **Platform:** GitHub Pages
- **Repository:** https://github.com/sancho16/docDianaSanchez.git
- **Branch:** `Prod` (production), `DevTurquoiseThemed` (development)
- **CDN:** Cloudflare for performance optimization

---

## 🔧 Backend Architecture

### Critical Dependency: Home Server

**⚠️ IMPORTANT:** The entire backend depends on a **home server** running at:
- **IP Address:** `192.168.0.131`
- **User:** `beckham23`
- **Location:** Physical home server (not cloud)

### Technology Stack
- **Python 3.10** - Core language
- **Flask** - Web framework
- **Gunicorn** - WSGI server
- **PostgreSQL** - Database
- **Cloudflare Tunnel** - Public access

### Backend Components

#### 1. Application Structure
```
diana-booking-backend/
├── app.py                  # Main Flask application
├── notify.py               # Email notification system
├── .env                    # Environment variables
├── requirements.txt        # Python dependencies
├── static/
│   └── robot.png          # Email assets
└── faker-env/             # Virtual environment
```

#### 2. Key API Endpoints
```http
GET  /                          # Health check
POST /api/bookings              # Create new booking
GET  /api/admin/bookings        # List all bookings (admin)
PATCH /api/admin/bookings/<id>  # Update booking status
PATCH /api/admin/bookings/<id>/mark-read  # Mark read/unread
GET  /api/admin/stats           # Dashboard statistics
GET  /admin                     # Admin login page
GET  /admin/view               # Admin dashboard
```

#### 3. Authentication System
- **Google OAuth** - Primary authentication method
- **Token-based** - Fallback authentication
- **Session Cookies** - Secure session management
- **Allowed Admins** - Email whitelist system

### Database Schema

#### Bookings Table
```sql
CREATE TABLE bookings (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    service TEXT NOT NULL,
    preferred_date DATE,
    preferred_time TEXT,
    message TEXT,
    status TEXT DEFAULT 'pending',
    is_dummy BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Valid Services
- Consulta General
- Medicina Preventiva
- Enfermedades Crónicas
- Atención Pediátrica
- Consulta Virtual
- Visita Domiciliaria

---

## 🏠 Home Server Configuration

### Critical Infrastructure Details

#### Server Specifications
- **Operating System:** Ubuntu Linux
- **Python Environment:** Virtual environment (`faker-env`)
- **Process Management:** Gunicorn with 2 workers
- **Network Access:** Cloudflare Tunnel for public exposure

#### Running Processes
```bash
# Backend server
/home/beckham23/faker-env/bin/python3 /home/beckham23/faker-env/bin/gunicorn -w 2 -b 127.0.0.1:8000 app:app

# Cloudflare tunnel (assumed)
# Exposes local port 8000 to https://api.docdianasanchez.com
```

#### Environment Configuration (.env)
```env
# Database
DATABASE_URL=postgresql://diana_app:diana_228d35464ad83ba0e3e3@127.0.0.1/diana_bookings

# Email (Gmail SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=osanchy7@gmail.com
SMTP_PASS=nxhzwytfyztuzmpj  # App-specific password
NOTIFY_TO=osanchy7@gmail.com  # Primary notification recipient

# Admin
ADMIN_TOKEN=ba19bba1878de076f13109e59c84574a2c900eea9d94731d
GOOGLE_CLIENT_ID=[Google OAuth Client ID]

# CORS
ALLOWED_ORIGINS=https://docdianasanchez.com,https://www.docdianasanchez.com
```

### Network Configuration
- **Local Binding:** 127.0.0.1:8000
- **Public Access:** Via Cloudflare Tunnel
- **Domain:** api.docdianasanchez.com
- **SSL:** Managed by Cloudflare

---

## 📧 Email System

### SMTP Configuration
- **Provider:** Gmail SMTP
- **Authentication:** App-specific password
- **Recipients:** 
  - Primary: osanchy7@gmail.com
  - Secondary: drasanchezd94@gmail.com

### Email Features
- **HTML Templates** - Professional glassmorphism design
- **Robot Footer** - Includes robot.png asset and emoji
- **Patient Information Cards** - Organized data display
- **Booking Details** - Service, date, time information
- **Admin Links** - Direct access to admin panel
- **Bilingual Support** - Spanish/English content

---

## 📊 Admin Panel Features

### Dashboard Components
1. **KPI Metrics**
   - Total real appointments
   - Pending appointments
   - Last 7 days activity
   - Dummy/test entries

2. **Data Visualization**
   - Appointments per day (Chart.js)
   - Status distribution
   - Service breakdown

3. **Booking Management**
   - Read/Unread system with visual indicators
   - Status updates (pending, confirmed, completed, cancelled)
   - Filter by status, read state, dummy entries
   - CSV export functionality

4. **Read/Unread System**
   - Visual indicators (red/green dots)
   - Filter buttons (All, Unread, Read)
   - Toggle actions (mark as read/unread)
   - Row highlighting for unread items

### Security Features
- **Google OAuth Integration** - Primary authentication
- **Token-based Fallback** - Alternative login method
- **Session Management** - Secure HTTP-only cookies
- **Admin Whitelist** - Email-based access control
- **CORS Protection** - Domain-restricted API access

---

## 🔄 Deployment Process

### Frontend Deployment
```bash
# 1. Development branch
git checkout DevTurquoiseThemed
# Make changes, test locally

# 2. Commit changes
git add -A
git commit -m "Feature description"
git push origin DevTurquoiseThemed

# 3. Production deployment
git checkout Prod
git merge DevTurquoiseThemed --no-ff -m "Deploy: feature"
git push origin Prod
# GitHub Pages automatically deploys from Prod branch
```

### Backend Deployment
```bash
# 1. Connect to home server
ssh beckham23@192.168.0.131

# 2. Navigate to backend directory
cd ~/diana-booking-backend

# 3. Update code (if needed)
# Make changes to app.py, notify.py, etc.

# 4. Restart services
pkill -f gunicorn
source faker-env/bin/activate
nohup gunicorn -w 2 -b 127.0.0.1:8000 app:app > app.log 2>&1 &
```

---

## ⚠️ Critical Dependencies & Risk Assessment

### Single Points of Failure

#### 1. Home Server Dependency
**Risk Level: HIGH**
- **Issue:** Entire backend depends on physical home server
- **Impact:** Complete service outage if server is offline
- **Mitigation Strategies:**
  - Monitor server uptime
  - Implement backup server
  - Consider cloud migration

#### 2. Internet Connection
**Risk Level: HIGH**
- **Issue:** Home internet outage affects backend
- **Impact:** API and admin panel become inaccessible
- **Mitigation:** Redundant internet connection or cloud hosting

#### 3. Cloudflare Tunnel
**Risk Level: MEDIUM**
- **Issue:** Tunnel failure breaks public API access
- **Impact:** Frontend cannot submit forms
- **Mitigation:** Direct IP access or alternative tunnel

#### 4. Database
**Risk Level: MEDIUM**
- **Issue:** Local PostgreSQL database
- **Impact:** Data loss risk, no automatic backups
- **Mitigation:** Regular database backups, cloud database option

### Recommendations for Improved Reliability

1. **Cloud Migration**
   - Move backend to AWS/DigitalOcean/Heroku
   - Use managed database service
   - Implement automatic scaling

2. **Backup Strategy**
   - Daily database backups
   - Configuration backups
   - Code repository mirrors

3. **Monitoring**
   - Uptime monitoring for API endpoints
   - Database health checks
   - Email notification alerts

4. **Load Balancing**
   - Multiple server instances
   - Database replication
   - CDN for static assets

---

## 🔧 Maintenance & Troubleshooting

### Common Issues & Solutions

#### Backend Server Down
```bash
# Check if server is running
ssh beckham23@192.168.0.131 "ps aux | grep gunicorn"

# Restart if needed
ssh beckham23@192.168.0.131 "cd ~/diana-booking-backend && pkill -f gunicorn && source faker-env/bin/activate && nohup gunicorn -w 2 -b 127.0.0.1:8000 app:app > app.log 2>&1 &"
```

#### Database Connection Issues
```bash
# Test database connection
ssh beckham23@192.168.0.131 "cd ~/diana-booking-backend && python3 -c 'import psycopg2; conn = psycopg2.connect(\"postgresql://diana_app:diana_228d35464ad83ba0e3e3@127.0.0.1/diana_bookings\"); print(\"Connection successful\")'"
```

#### Email Notifications Not Sending
```bash
# Check environment variables
ssh beckham23@192.168.0.131 "cd ~/diana-booking-backend && grep SMTP .env"

# Test email function
ssh beckham23@192.168.0.131 "cd ~/diana-booking-backend && python3 -c 'import notify; print(notify.send_booking_notice({\"id\": 999, \"name\": \"Test\", \"phone\": \"+506 9999-0000\", \"email\": \"test@test.com\", \"service\": \"Test\", \"preferred_date\": \"2026-07-25\", \"preferred_time\": \"10:00\", \"message\": \"Test message\"}))'"
```

### Log Locations
- **Application Logs:** `~/diana-booking-backend/app.log`
- **System Logs:** `/var/log/syslog` (on server)
- **Frontend Logs:** Browser Developer Console

### Backup Procedures

#### Database Backup
```bash
# Create backup
ssh beckham23@192.168.0.131 "pg_dump diana_bookings > diana_bookings_backup_$(date +%Y%m%d).sql"

# Restore from backup
ssh beckham23@192.168.0.131 "psql diana_bookings < diana_bookings_backup_YYYYMMDD.sql"
```

#### Configuration Backup
```bash
# Backup environment and code
ssh beckham23@192.168.0.131 "cd ~/diana-booking-backend && tar -czf backup_$(date +%Y%m%d).tar.gz *.py .env requirements.txt"
```

---

## 📱 Frontend Features Deep Dive

### Modern Date/Time Picker
- **Interactive Time Slots:** Visual grid instead of dropdown
- **Haptic Feedback:** Device vibration on selection (mobile)
- **Glassmorphism Design:** Modern translucent styling
- **Responsive Grid:** Adaptive layout for all screen sizes
- **Accessibility:** Keyboard navigation and ARIA labels

### Bilingual System (i18n)
- **Dynamic Switching:** Real-time language toggle
- **LocalStorage Persistence:** Remembers user preference
- **Complete Translation:** All UI elements covered
- **HTML Content:** Supports rich HTML in translations

### Service Cards
- **Flip Animation:** 3D flip effect on hover/tap
- **Progressive Enhancement:** Works without JavaScript
- **Accessibility:** Proper ARIA labels and focus management
- **Mobile Optimized:** Touch-friendly interactions

### Form Validation
- **Real-time Validation:** Immediate feedback
- **Service Matching:** Backend validation sync
- **Phone Format:** Costa Rican phone number format
- **Date Restrictions:** Future dates only
- **Required Fields:** Clear visual indicators

---

## 🔒 Security Implementation

### Frontend Security
- **HTTPS Enforcement:** All connections encrypted
- **Content Security Policy:** XSS protection
- **Form Validation:** Client and server-side
- **CORS Headers:** Domain restriction

### Backend Security
- **Input Sanitization:** SQL injection prevention
- **Rate Limiting:** Prevents spam submissions
- **Authentication:** Multi-layer admin access
- **Session Security:** HTTP-only secure cookies

### Database Security
- **User Permissions:** Limited database user
- **Connection Encryption:** SSL connections
- **Input Validation:** Parameterized queries
- **Access Control:** Network-level restrictions

---

## 📈 Performance Optimization

### Frontend Optimization
- **Static Assets:** Optimized images and minified CSS/JS
- **CDN Delivery:** Cloudflare global distribution
- **Caching Strategy:** Browser and CDN caching
- **Lazy Loading:** Images loaded on demand

### Backend Optimization
- **Connection Pooling:** PostgreSQL connection management
- **Gunicorn Workers:** Multiple worker processes
- **Static File Serving:** Direct file serving
- **Database Indexing:** Query optimization

### Monitoring Metrics
- **Response Times:** API endpoint performance
- **Error Rates:** Failed requests tracking
- **Database Performance:** Query execution times
- **User Experience:** Form submission success rates

---

## 🎯 Future Improvements

### Short Term (1-3 months)
1. **Cloud Database Migration**
   - Move PostgreSQL to managed cloud service
   - Implement automatic backups
   - Add read replicas for better performance

2. **Enhanced Monitoring**
   - Application performance monitoring (APM)
   - Real-time alerting system
   - Dashboard for system health

3. **Mobile App**
   - PWA implementation
   - Offline form storage
   - Push notifications

### Long Term (3-12 months)
1. **Full Cloud Migration**
   - Backend hosting on cloud platform
   - Auto-scaling capabilities
   - Global CDN distribution

2. **Advanced Features**
   - Video consultation booking
   - Patient portal with login
   - Integration with medical records

3. **AI Integration**
   - Chatbot for initial screening
   - Appointment optimization
   - Automated follow-ups

---

## 💰 Cost Analysis

### Current Costs (Monthly)
- **GitHub Pages:** Free
- **Cloudflare:** Free tier
- **Home Server:** Electricity (~$30)
- **Domain Registration:** ~$15/year
- **Gmail SMTP:** Free

**Total Monthly Cost: ~$30**

### Cloud Migration Estimate
- **DigitalOcean Droplet:** $20/month
- **Managed PostgreSQL:** $15/month
- **Backup Storage:** $5/month
- **CDN/Load Balancer:** $10/month

**Estimated Cloud Cost: ~$50/month**

---

## 📞 Support & Contact Information

### Technical Support
- **Repository:** https://github.com/sancho16/docDianaSanchez
- **Issues:** GitHub Issues section
- **Documentation:** This document

### Server Access
- **SSH Access:** beckham23@192.168.0.131
- **Home Server Location:** Physical location required
- **Admin Panel:** https://api.docdianasanchez.com/admin

### Emergency Procedures
1. **Server Offline:** Contact home server location
2. **Database Issues:** SSH access required for troubleshooting
3. **DNS Problems:** Check Cloudflare tunnel status
4. **Email Issues:** Verify Gmail SMTP credentials

---

## 📚 Conclusion

The Dr. Diana Sánchez website represents a modern, full-stack web application that successfully bridges frontend user experience with robust backend functionality. While the current home server setup provides cost-effective operation, the architecture is designed to scale and can be easily migrated to cloud infrastructure when needed.

The system's strength lies in its simplicity and reliability, with comprehensive admin features and professional presentation. The main risk factor is the dependency on home server infrastructure, which should be addressed in future iterations.

**Key Success Factors:**
- ✅ Professional medical website with modern UX
- ✅ Comprehensive booking and admin system
- ✅ Bilingual support for Costa Rican market
- ✅ Cost-effective current operation
- ✅ Scalable architecture for future growth

**Next Steps:**
1. Implement monitoring and backup procedures
2. Plan cloud migration strategy
3. Document standard operating procedures
4. Set up automated deployment pipelines

---

*Document Version: 1.0*  
*Last Updated: July 22, 2026*  
*Architecture Status: Production Ready*