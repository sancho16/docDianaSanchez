# 🚀 Enterprise Deployment Guide

## Overview

This guide explains the proper deployment workflow for the Dr. Diana Sánchez medical practice website.

---

## 🏗️ Current Architecture

### Production Environment
```
┌─────────────────────────────────────────┐
│           PRODUCTION                    │
├─────────────────────────────────────────┤
│ Frontend: docdianasanchez.com           │
│  └─ GitHub Pages (main branch)          │
│                                         │
│ Backend API: api.docdianasanchez.com    │
│  └─ beckham23@192.168.0.131:8000        │
│  └─ Database: diana_bookings (MySQL)    │
│  └─ Real patient data                   │
└─────────────────────────────────────────┘
```

---

## ⚠️ Current Problem

**Issue**: Changes pushed to `main` branch automatically deploy to production
- No testing phase before going live
- Risk of breaking live website
- No way to show changes to stakeholders before deployment

---

## ✅ Recommended Solution: Add Staging Environment

### Proposed Architecture

```
┌──────────────────────────────────────────────────────┐
│                   DEVELOPMENT                        │
│  • Your laptop                                       │
│  • Feature branches (DevTurquoiseThemed, etc.)       │
│  • Test everything locally first                     │
└──────────────────────────────────────────────────────┘
                        ↓
                    git push
                    Create PR
                        ↓
┌──────────────────────────────────────────────────────┐
│                    STAGING                           │
│  Frontend: staging.docdianasanchez.com               │
│   └─ Deploy from 'staging' branch                    │
│                                                      │
│  Backend: api.docdianasanchez.com:8001               │
│   └─ Separate Flask instance                         │
│   └─ Database: diana_bookings_staging (test data)    │
│                                                      │
│  Purpose:                                            │
│   • Test before going live                           │
│   • Show to Dr. Diana for approval                   │
│   • QA testing                                       │
│   • No risk to real patients                         │
└──────────────────────────────────────────────────────┘
                        ↓
                  Manual approval
                    Merge PR
                        ↓
┌──────────────────────────────────────────────────────┐
│                  PRODUCTION                          │
│  Frontend: docdianasanchez.com                       │
│   └─ Deploy from 'main' branch                       │
│                                                      │
│  Backend: api.docdianasanchez.com:8000               │
│   └─ Production Flask instance                       │
│   └─ Database: diana_bookings (REAL patient data)    │
│                                                      │
│  Purpose:                                            │
│   • Serve real patients                              │
│   • Only deploy tested code                          │
│   • Maximum reliability                              │
└──────────────────────────────────────────────────────┘
```

---

## 📋 Implementation Steps

### Step 1: Create Staging Branch

```bash
git checkout main
git pull origin main
git checkout -b staging
git push origin staging
```

### Step 2: Setup Staging Backend

SSH into server:
```bash
ssh beckham23@192.168.0.131
```

Clone repository for staging:
```bash
cd ~
git clone https://github.com/sancho16/docDianaSanchez.git diana-booking-staging
cd diana-booking-staging
git checkout staging
```

Create staging database:
```bash
mysql -u beckham23 -p
CREATE DATABASE diana_bookings_staging;
USE diana_bookings_staging;
-- Copy schema from production
-- INSERT test data only
EXIT;
```

Create staging `.env`:
```bash
cd ~/diana-booking-staging
cp ~/diana-booking-backend/.env .env
nano .env
```

Edit `.env` for staging:
```
# Staging Environment
DATABASE_HOST=localhost
DATABASE_USER=beckham23
DATABASE_PASSWORD=your_password
DATABASE_NAME=diana_bookings_staging
PORT=8001
ENVIRONMENT=staging
```

Start staging server:
```bash
cd ~/diana-booking-staging
nohup python3 app.py > staging.log 2>&1 &
```

### Step 3: Configure Nginx for Staging

```bash
sudo nano /etc/nginx/sites-available/staging-api
```

Add:
```nginx
server {
    listen 80;
    server_name staging-api.docdianasanchez.com;
    
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Enable and reload:
```bash
sudo ln -s /etc/nginx/sites-available/staging-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 4: Setup Staging Frontend

**Option A: GitHub Pages with staging subdomain**
1. Create `gh-pages-staging` branch
2. Configure custom domain: `staging.docdianasanchez.com`

**Option B: Netlify/Vercel (Recommended)**
1. Connect GitHub repository
2. Set branch to deploy: `staging`
3. Auto-deploy on push

---

## 🔄 Daily Workflow

### Developing a New Feature

```bash
# 1. Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/new-cool-feature

# 2. Make changes, commit
git add .
git commit -m "feat: add new cool feature"
git push origin feature/new-cool-feature

# 3. Create PR to staging branch
gh pr create --base staging --head feature/new-cool-feature

# 4. Merge to staging (auto-deploys to staging environment)
gh pr merge <PR_NUMBER>

# 5. Test on staging.docdianasanchez.com

# 6. If tests pass, create PR from staging to main
gh pr create --base main --head staging

# 7. Review, approve, merge (deploys to production)
gh pr merge <PR_NUMBER>
```

### Hotfix (Emergency Production Fix)

```bash
# 1. Create hotfix branch from main
git checkout main
git checkout -b hotfix/critical-bug

# 2. Fix the bug
git add .
git commit -m "fix: critical bug in booking form"

# 3. PR directly to main (skip staging for emergencies)
gh pr create --base main --head hotfix/critical-bug

# 4. Fast review and merge
gh pr merge <PR_NUMBER>

# 5. Backport to staging
git checkout staging
git merge main
git push origin staging
```

---

## 🎯 Branch Strategy

```
main (production)
├── Always deployable
├── Protected branch (require PR + approval)
└── Auto-deploys to production

staging (pre-production)
├── Integration testing
├── Show to stakeholders
└── Auto-deploys to staging environment

feature/* (development)
├── Individual features
└── Merge to staging first

hotfix/* (emergency fixes)
├── Critical production fixes
└── Can merge directly to main (then backport)
```

---

## ✅ Checklist Before Deploying to Production

- [ ] Code reviewed by at least 1 person
- [ ] Tested on staging environment
- [ ] No console errors in browser
- [ ] Mobile responsiveness verified (iPhone/Android)
- [ ] Form submissions tested
- [ ] Database queries optimized
- [ ] No sensitive data exposed (API keys, passwords)
- [ ] Shown to Dr. Diana for approval (if UI changes)
- [ ] Documentation updated
- [ ] Database backups taken

---

## 🔐 Security Considerations

### Sensitive Data
- Never commit `.env` files
- Use environment variables for secrets
- Keep staging and production databases separate
- Different API keys for staging vs production

### HIPAA Compliance (Medical Data)
- Encrypt patient data at rest and in transit
- Audit logs for data access
- Regular security reviews
- No patient data in staging (use anonymized test data)

---

## 📊 Deployment Frequency

**Recommended**:
- Deploy to staging: Multiple times per day (as needed)
- Deploy to production: 2-3 times per week (planned)
- Hotfixes to production: As needed (emergency only)

---

## 🆘 Rollback Procedure

If something breaks in production:

```bash
# Option 1: Revert the commit
git revert <bad_commit_hash>
git push origin main

# Option 2: Roll back to previous version
git checkout main
git reset --hard <previous_good_commit>
git push origin main --force

# Option 3: Deploy previous release tag
git checkout tags/v1.2.0
git push origin main --force
```

---

## 📝 Summary

**Current State**: Direct deployment to production (risky)
**Recommended State**: Staging → Testing → Production (safe)

**Next Steps**:
1. Set up staging environment (1-2 hours)
2. Test the workflow with a small change
3. Train team on new process
4. Document any project-specific variations

This protects your patients and gives you confidence that changes work before going live!
