# 🧪 TEST CHECKLIST - Admin Panel Updates
## Quick Verification Guide

---

## 🎯 WHAT TO TEST

### 1️⃣ Perfect Circle Charts
**URL**: https://api.docdianasanchez.com/admin/view

**Steps**:
1. Log in with Google or admin token
2. Scroll to the charts section
3. Look at the "By Status" chart (right panel)
4. Look at the "Real vs. Dummy" chart (bottom right)

**✅ Expected Result**:
- Both charts should be **perfectly circular** (not elliptical)
- Should remain circular when you resize the browser window
- Should look circular on phone/tablet too

**❌ If Not Working**:
- Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)
- Try incognito/private mode
- Check browser console for errors

---

### 2️⃣ Clickable Appointment Rows
**URL**: https://api.docdianasanchez.com/admin/view

**Steps**:
1. Scroll down to the appointments table
2. Hover over any appointment row
3. Click on the row (NOT on the dropdown)

**✅ Expected Result**:
- Row should highlight with **turquoise color** on hover
- Click should open a **new tab** (1400x900 window)
- New tab URL should be: `/admin/medical-records?booking_id=123`

**❌ If Not Working**:
- Check if JavaScript is enabled
- Look for console errors (F12 → Console tab)
- Try clicking different rows

---

### 3️⃣ Medical Records Page
**URL**: Opens automatically when you click an appointment

**Steps**:
1. Click any appointment row (from step 2)
2. Wait for new tab to open
3. Review the medical records page

**✅ Expected Result**:
- **Left panel** shows medical record form with:
  - Patient name, email, phone (pre-filled)
  - Service and appointment date/time (pre-filled)
  - Empty form fields for diagnosis, treatment, etc.
  - "Save Medical Record" button
  - "Cancel" button
  
- **Right panel** shows booking details:
  - Appointment status (#ID, Created date)
  - Device tracking info (IP, location, browser, OS)
  - Visit location if provided

**❌ If Not Working**:
- Check URL has `?booking_id=` parameter
- Verify you're still logged in
- Look at server logs on 192.168.0.131

---

### 4️⃣ Form Functionality
**URL**: In the medical records tab

**Steps**:
1. Fill in the required fields:
   - Diagnosis (required)
   - Treatment Plan (required)
2. Optionally fill other fields
3. Click "Save Medical Record"

**✅ Expected Result**:
- Alert should say "Medical record saved successfully!"
- Tab should close automatically
- Data should be saved to database

**❌ If Not Working**:
- Check browser console for errors
- Verify network request went to `/api/admin/visits`
- Check server is accepting POST requests

---

### 5️⃣ Mobile Testing (iPhone)
**URL**: https://api.docdianasanchez.com/admin/view

**Steps**:
1. Open in Safari on iPhone
2. Log in
3. Tap an appointment row

**✅ Expected Result**:
- New tab opens with medical records
- Layout is responsive (single column on phone)
- All text is readable
- Form fields are touch-friendly

**❌ If Not Working**:
- Try landscape orientation
- Check if popups are blocked
- Verify mobile data/WiFi connection

---

## 🔍 QUICK DIAGNOSTICS

### Check If Server is Running:
```bash
ssh beckham23@192.168.0.131 "ps aux | grep gunicorn"
```
**Should show**: Multiple Python/gunicorn processes

### Check If Route Exists:
```bash
ssh beckham23@192.168.0.131 "grep -c 'medical-records' ~/diana-booking-backend/app.py"
```
**Should show**: Number > 0

### View Recent Logs:
```bash
ssh beckham23@192.168.0.131 "tail -20 /var/log/diana-booking-backend.log"
```
**Should show**: No errors, successful requests

### Verify Charts CSS:
Open browser DevTools (F12) → Elements → Search for `.chart-circle`
**Should show**: `aspect-ratio: 1/1` in the styles

---

## 📊 SUCCESS INDICATORS

### ✅ Everything Working:
- [ ] Charts are perfect circles
- [ ] Rows highlight on hover
- [ ] Clicking row opens new tab
- [ ] Medical records page loads
- [ ] Patient data is pre-filled
- [ ] Form can be submitted
- [ ] Works on iPhone

### ⚠️ Partial Issues:
- Charts circular on desktop but not mobile → Browser compatibility
- Rows clickable but no new tab → Popup blocker
- Page loads but no data → Database connection issue

### ❌ Major Problems:
- Page not found → Route not deployed
- Charts not circular → CSS not applied
- Rows not clickable → JavaScript not loaded

---

## 🛠️ EMERGENCY FIXES

### Problem: Medical Records Page 404
**Solution**:
```bash
ssh beckham23@192.168.0.131
cd ~/diana-booking-backend
grep '@app.route("/admin/medical-records"' app.py
# If not found, re-run deployment script
python3 add_route_manual.py app.py
touch app.py
```

### Problem: Charts Not Circular
**Solution**:
```bash
# Clear cache: Ctrl+Shift+Del (Windows) or Cmd+Shift+Del (Mac)
# Then reload with Ctrl+Shift+R or Cmd+Shift+R
```

### Problem: Rows Not Clickable
**Solution**:
Open browser console (F12), check for:
- `openMedicalRecord is not defined` → JavaScript didn't load
- Click doesn't work → Check if `onclick` attribute exists on `<tr>` elements

### Problem: Server Not Responding
**Solution**:
```bash
ssh beckham23@192.168.0.131
sudo systemctl restart diana-booking-backend
# Wait 10 seconds
curl http://localhost:8000/api/health
```

---

## 📞 SUPPORT

If tests fail and emergency fixes don't work:

1. **Check GitHub**: https://github.com/sancho16/docDianaSanchez
2. **Review docs**: ADMIN_VIEW_UPDATES.md
3. **Server logs**: `tail -f /var/log/diana-booking-backend.log`
4. **Rollback**: Use backup files on server (`app.py.backup-*`)

---

## ✅ SIGN-OFF

After testing, mark completion:

**Tester**: ________________  
**Date**: ________________  
**Status**: ☐ All Passed  ☐ Minor Issues  ☐ Major Issues  

**Notes**:
_______________________________________________________
_______________________________________________________
_______________________________________________________

---

**Last Updated**: July 23, 2026  
**Version**: 2.1.0
