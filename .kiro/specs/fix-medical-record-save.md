# Fix Medical Record Save Functionality

## Overview
Fix the medical record save button to properly update visit records, mark bookings as completed, and capture/display IP address and device information in booking cards.

## Current Issues

### 1. Missing `/complete` Endpoint
- Frontend calls `POST /api/admin/visits/<id>/complete` 
- Backend doesn't have this endpoint implemented
- Results in 404 error when completing visits

### 2. Missing `chief_complaint` Field
- Frontend form has "Chief Complaint" textarea
- Not included in `visitData` object sent to backend
- Backend `admin_update_visit()` doesn't process this field

### 3. Booking Not Marked as Completed
- When visit is completed, the related booking should be marked as "completed"
- Currently booking status remains "pending" or "confirmed"

### 4. IP/Device Tracking Not Captured
- Frontend booking form doesn't capture IP address and device info
- Backend booking cards show placeholder for tracking info but data isn't collected
- Need to capture: IP address, location (city/country), device type, OS, browser

## Requirements

### Backend Changes

#### 1. Add `/complete` Endpoint
```python
@app.route("/api/admin/visits/<int:visit_id>/complete", methods=["POST"])
def admin_complete_visit(visit_id):
    """Complete visit, update booking status, and send summary email"""
    if not _admin_authed():
        return jsonify({"error": "unauthorized"}), 401
    
    try:
        conn = _db()
        cur = conn.cursor()
        
        # Get visit with booking ID
        cur.execute("""
            SELECT booking_id FROM visits WHERE id = %s
        """, (visit_id,))
        result = cur.fetchone()
        
        if not result:
            return jsonify({"error": "Visit not found"}), 404
        
        booking_id = result[0]
        
        # Update visit status to completed
        cur.execute("""
            UPDATE visits 
            SET visit_status = 'completed', updated_at = NOW() 
            WHERE id = %s
        """, (visit_id,))
        
        # Update related booking status to completed
        cur.execute("""
            UPDATE bookings 
            SET status = 'completed', updated_at = NOW() 
            WHERE id = %s
        """, (booking_id,))
        
        conn.commit()
        cur.close()
        conn.close()
        
        # Send email notification (existing notify.py logic)
        try:
            notify.send_visit_completion_notice({...})
        except Exception as e:
            print(f"Email notification failed: {e}")
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

#### 2. Fix `admin_update_visit()` to Include `chief_complaint`
```python
# In admin_update_visit(), add to field list:
for field in ["chief_complaint", "symptoms", "vital_signs", ...]:
```

#### 3. Add IP/Device Capture to Booking Creation
```python
# In create_booking(), capture device info:
ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
user_agent = request.headers.get('User-Agent', '')

# Parse user agent for device info (use user_agents library)
from user_agents import parse
ua = parse(user_agent)

# Store in bookings table:
INSERT INTO bookings (..., ip_address, device_type, device_os, device_browser, ...)
VALUES (..., %s, %s, %s, %s, ...)
```

### Frontend Changes

#### 1. Fix `medical-records.js` `submitVisit()`
```javascript
async submitVisit() {
    // First save all current progress INCLUDING chief_complaint
    await this.saveProgress(false);

    if (!this.validateForm()) {
        this.showNotification('Please fill in all required fields', 'error');
        return;
    }

    try {
        const response = await fetch(`/api/admin/visits/${this.visitId}/complete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const result = await response.json();

        if (response.ok) {
            this.showNotification('Visit completed! Booking marked as complete.', 'success');
            setTimeout(() => window.close(), 2000);
        } else {
            throw new Error(result.error || 'Failed to complete visit');
        }
    } catch (error) {
        console.error('Error completing visit:', error);
        this.showNotification('Error completing visit: ' + error.message, 'error');
    }
}
```

#### 2. Fix `saveProgress()` to Include `chief_complaint`
```javascript
async saveProgress(showConfirmation = true) {
    if (!this.visitId) return;

    const visitData = {
        chief_complaint: document.getElementById('chief-complaint').value, // ← ADD THIS
        physical_examination: document.getElementById('physical-examination').value,
        diagnosis: document.getElementById('diagnosis').value,
        treatment_plan: document.getElementById('treatment-plan').value,
        follow_up_instructions: document.getElementById('follow-up-instructions').value,
        doctor_notes: document.getElementById('doctor-notes').value,
        next_appointment: document.getElementById('next-appointment').value || null,
        visit_status: 'in_progress'
    };
    
    // ... rest of save logic
}
```

#### 3. Add Client-Side IP/Device Capture to Booking Form
```javascript
// In index.html booking form submission:
async function captureDeviceInfo() {
    // Get IP from external service
    const ipResponse = await fetch('https://api.ipify.org?format=json');
    const { ip } = await ipResponse.json();
    
    // Get location from IP
    const geoResponse = await fetch(`https://ipapi.co/${ip}/json/`);
    const geo = await geoResponse.json();
    
    // Parse user agent
    const ua = navigator.userAgent;
    
    return {
        ip_address: ip,
        ip_city: geo.city,
        ip_country: geo.country_name,
        device_type: /Mobile|Android|iPhone/i.test(ua) ? 'mobile' : 'desktop',
        device_os: getOS(ua),
        device_browser: getBrowser(ua)
    };
}

// Include in booking submission:
const deviceInfo = await captureDeviceInfo();
const bookingData = { ...formData, ...deviceInfo };
```

#### 4. Display Tracking Info in Booking Cards (Already Implemented)
The `admin.js` already has the `trackingHTML` section in `buildAppointmentCard()` that displays:
- 🌐 IP address and location
- 📱 Device type and brand
- 💻 OS and browser

Just need to ensure data is being passed from backend.

## Database Schema Updates

```sql
-- Add tracking columns to bookings table if not exist:
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS ip_address VARCHAR(45);
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS ip_city VARCHAR(100);
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS ip_country VARCHAR(100);
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS device_type VARCHAR(50);
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS device_os VARCHAR(100);
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS device_browser VARCHAR(100);
```

## Testing Checklist

- [ ] Fill out medical record form with all fields including chief complaint
- [ ] Click "Save Progress" - verify data persists in database
- [ ] Click "Complete Visit & Send Summary"
  - [ ] Verify visit status changed to "completed"
  - [ ] Verify booking status changed to "completed"
  - [ ] Verify email notification sent
  - [ ] Verify window closes after success
- [ ] Create new booking from public form
  - [ ] Verify IP address captured
  - [ ] Verify device type, OS, browser captured
  - [ ] Verify location (city/country) captured
- [ ] View booking card in admin panel
  - [ ] Verify tracking info displayed with icons
  - [ ] Verify IP, location, device details visible

## Success Criteria

1. ✅ Medical record "Complete Visit" button updates visit status to "completed"
2. ✅ Related booking status updates to "completed" 
3. ✅ Chief complaint field saves properly
4. ✅ IP address, device type, OS, and browser captured on booking creation
5. ✅ Tracking info displayed in booking card details with icons
6. ✅ Email notification sent on visit completion
7. ✅ No console errors on submit
8. ✅ Success message shows before window closes

## Technical Notes

- Use `user-agents` Python library for UA parsing: `pip install pyyaml ua-parser user-agents`
- Use `ipapi.co` free tier for IP geolocation (no API key needed)
- For client-side IP capture, use `api.ipify.org` (free, no auth)
- Store IP as VARCHAR(45) to support IPv6 addresses
- Add indexes on booking status and visit status for query performance
