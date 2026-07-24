# Email Notification Setup Guide
## Dr. Diana Sánchez Booking System

## Problem Identified
Your appointment booking system was showing success messages but **emails were not being sent** because:
1. ❌ The `notify.py` module was missing
2. ❌ SMTP email configuration was not set up
3. ❌ No email credentials were configured

## What Was Fixed

### 1. Created `notify.py` Module ✓
A new email notification system that:
- Sends appointment confirmations to patients
- Sends booking notifications to Dr. Diana
- Sends visit completion summaries
- Includes beautiful HTML email templates
- Has proper error handling and logging

### 2. Updated Configuration Files ✓
- Updated `.env.example` with all required SMTP settings
- Updated `requirements.txt` with correct dependencies
- Fixed PostgreSQL configuration

## Setup Instructions

### Step 1: Install Dependencies
```bash
cd /Users/juliansanchez/docDianaSanchez/backend
pip install -r requirements.txt
```

### Step 2: Create Gmail App Password
**Important:** Gmail requires an "App Password" for SMTP access, not your regular password.

1. Go to your Google Account: https://myaccount.google.com/
2. Click "Security" in the left menu
3. Under "Signing in to Google", click "2-Step Verification"
   - **Enable 2-Step Verification if not already enabled**
4. Once 2-Step is enabled, go back to Security
5. Click "App passwords" (at the bottom)
6. Select:
   - App: **Mail**
   - Device: **Other** (type "Dr Diana Backend")
7. Click "Generate"
8. **Copy the 16-character password** (it will look like: `abcd efgh ijkl mnop`)
9. Save this password - you'll need it for the `.env` file

### Step 3: Create `.env` File
Create a file called `.env` in the backend directory:

```bash
cd /Users/juliansanchez/docDianaSanchez/backend
cp .env.example .env
nano .env  # or use your preferred editor
```

### Step 4: Configure Email Settings
Edit the `.env` file and add your email configuration:

```bash
# Database Configuration
DATABASE_URL=postgresql://diana_app@localhost/diana_bookings

# Server Configuration
PORT=8000
ENVIRONMENT=production
ALLOWED_ORIGINS=https://docdianasanchez.com,https://www.docdianasanchez.com

# Admin Configuration
ADMIN_TOKEN=your_secure_admin_token_here
GOOGLE_CLIENT_ID=your_google_client_id_here
ALLOWED_ADMINS=drasanchezd94@gmail.com

# Email (SMTP) Configuration - REQUIRED FOR EMAIL NOTIFICATIONS
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=drasanchezd94@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop  # Replace with your App Password from Step 2
SMTP_FROM_EMAIL=drasanchezd94@gmail.com
SMTP_FROM_NAME=Dr. Diana Sánchez
DOCTOR_EMAIL=drasanchezd94@gmail.com

# WhatsApp Configuration (fallback notification)
WHATSAPP_NOTIFICATION=true
DOCTOR_WHATSAPP=+50683493378
```

**Important Notes:**
- Replace `abcd efgh ijkl mnop` with the actual App Password from Step 2
- Remove spaces from the App Password when pasting
- Keep the `.env` file secure - never commit it to git

### Step 5: Test Email Configuration
Test that emails are working:

```bash
cd /Users/juliansanchez/docDianaSanchez/backend
python3 notify.py
```

This will show your configuration and send a test email.

### Step 6: Restart the Backend Server
After configuration, restart your backend:

```bash
# If using the deployment script
./restart_backend.sh

# Or manually
pkill -f "python.*app.py"
python3 app.py
```

## Verification

### Test the Complete Flow
1. Go to https://docdianasanchez.com
2. Scroll to the contact form
3. Fill out an appointment request
4. Submit the form
5. Check:
   - ✓ Success message appears on the website
   - ✓ Dr. Diana receives notification email at drasanchezd94@gmail.com
   - ✓ Patient receives confirmation email (if email provided)

## Email Templates

The system sends two types of emails:

### 1. Doctor Notification
When a patient submits an appointment:
- **To:** drasanchezd94@gmail.com
- **Subject:** 🏥 Nueva Cita: [Patient Name] - [Service]
- **Contains:** Patient info, service, preferred date/time, message
- **CTA:** Link to admin panel

### 2. Patient Confirmation
When a patient submits an appointment (if email provided):
- **To:** Patient's email
- **Subject:** ✓ Solicitud de Cita Recibida - Dr. Diana Sánchez
- **Contains:** Booking confirmation, next steps, WhatsApp link
- **Response time:** 24-48 hours

## Troubleshooting

### "SMTP not configured" Error
```
[notify] SMTP not configured - email notifications disabled
```
**Solution:** Check that `SMTP_USERNAME` and `SMTP_PASSWORD` are set in `.env`

### "Authentication failed" Error
```
smtplib.SMTPAuthenticationError: (535, b'5.7.8 Username and Password not accepted')
```
**Solutions:**
1. Make sure you're using an **App Password**, not your regular Gmail password
2. Verify 2-Step Verification is enabled on your Google Account
3. Check that the App Password is correct (no spaces)
4. Try generating a new App Password

### "Connection refused" Error
```
ConnectionRefusedError: [Errno 61] Connection refused
```
**Solutions:**
1. Check your internet connection
2. Verify SMTP server and port: `smtp.gmail.com:587`
3. Check if your firewall is blocking port 587

### Emails Going to Spam
If emails are going to spam:
1. Ask recipients to mark emails as "Not Spam"
2. Consider adding SPF and DKIM records to your domain
3. Ensure `SMTP_FROM_EMAIL` matches `SMTP_USERNAME`

### Check Backend Logs
Monitor the backend for email sending status:
```bash
tail -f /path/to/backend/logs/app.log
```

Look for lines like:
- `[notify] ✓ Doctor notification sent to ...`
- `[notify] ✓ Patient confirmation sent to ...`
- `[notify] ✗ Email sending failed: ...`

## Alternative: Using SendGrid or Other SMTP Services

If you prefer to use SendGrid, Mailgun, or another service instead of Gmail:

1. Update `.env` with your service's SMTP settings:
```bash
# SendGrid example
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your_sendgrid_api_key
SMTP_FROM_EMAIL=drasanchezd94@gmail.com
```

2. No code changes needed - `notify.py` works with any SMTP server

## Security Best Practices

✓ **Never commit `.env` to git** - it contains sensitive credentials
✓ **Use App Passwords** - not your main Gmail password
✓ **Rotate passwords regularly** - generate new App Passwords periodically
✓ **Monitor email logs** - watch for suspicious activity
✓ **Keep dependencies updated** - run `pip install -U -r requirements.txt`

## Support

If you continue having issues:
1. Check the backend logs for detailed error messages
2. Test with `python3 notify.py` to isolate email issues
3. Verify database connectivity separately
4. Check that the backend is actually running and accessible

## Summary

**Before:** ❌ Bookings saved but no emails sent
**After:** ✓ Complete notification system with beautiful HTML emails

The system now:
- ✓ Sends booking notifications to Dr. Diana
- ✓ Sends confirmations to patients
- ✓ Includes WhatsApp fallback
- ✓ Has proper error handling
- ✓ Logs all email activity
- ✓ Uses professional HTML templates

**Next Step:** Configure your `.env` file with the Gmail App Password from Step 2!
