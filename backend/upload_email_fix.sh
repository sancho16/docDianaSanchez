#!/bin/bash
# Upload email notification fix to server
# Dr. Diana Sánchez Booking System

set -e  # Exit on error

SERVER="beckham23@192.168.0.131"
BACKEND_DIR="~/diana-booking-backend"

echo "========================================"
echo "Email Fix Upload Script"
echo "Dr. Diana Sánchez Booking System"
echo "========================================"
echo ""

# Check if files exist
echo "1. Checking local files..."
if [ ! -f "notify.py" ]; then
    echo "❌ Error: notify.py not found in current directory"
    echo "   Please run this script from the backend/ directory"
    exit 1
fi
echo "✓ notify.py found"

if [ -f "test_email.py" ]; then
    echo "✓ test_email.py found"
    UPLOAD_TEST=true
else
    echo "⚠ test_email.py not found (optional)"
    UPLOAD_TEST=false
fi

echo ""

# Upload notify.py
echo "2. Uploading notify.py to server..."
scp notify.py ${SERVER}:${BACKEND_DIR}/
if [ $? -eq 0 ]; then
    echo "✓ notify.py uploaded successfully"
else
    echo "❌ Failed to upload notify.py"
    exit 1
fi

echo ""

# Upload test_email.py if exists
if [ "$UPLOAD_TEST" = true ]; then
    echo "3. Uploading test_email.py to server..."
    scp test_email.py ${SERVER}:${BACKEND_DIR}/
    if [ $? -eq 0 ]; then
        echo "✓ test_email.py uploaded successfully"
        # Make it executable
        ssh ${SERVER} "chmod +x ${BACKEND_DIR}/test_email.py"
        echo "✓ Made test_email.py executable"
    else
        echo "⚠ Failed to upload test_email.py (non-critical)"
    fi
    echo ""
fi

# Upload documentation if exists
if [ -f "EMAIL_SETUP_GUIDE.md" ]; then
    echo "4. Uploading EMAIL_SETUP_GUIDE.md..."
    scp EMAIL_SETUP_GUIDE.md ${SERVER}:${BACKEND_DIR}/
    if [ $? -eq 0 ]; then
        echo "✓ EMAIL_SETUP_GUIDE.md uploaded"
    fi
    echo ""
fi

# Verify files on server
echo "5. Verifying files on server..."
ssh ${SERVER} "ls -lh ${BACKEND_DIR}/notify.py ${BACKEND_DIR}/test_email.py 2>/dev/null || ls -lh ${BACKEND_DIR}/notify.py"
echo ""

echo "========================================"
echo "✅ Upload Complete!"
echo "========================================"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Configure email settings:"
echo "   ssh ${SERVER}"
echo "   nano ${BACKEND_DIR}/.env"
echo ""
echo "   Add these lines:"
echo "   SMTP_USERNAME=drasanchezd94@gmail.com"
echo "   SMTP_PASSWORD=your_gmail_app_password_here"
echo "   DOCTOR_EMAIL=drasanchezd94@gmail.com"
echo ""
echo "2. Generate Gmail App Password:"
echo "   https://myaccount.google.com/apppasswords"
echo ""
echo "3. Test email configuration:"
echo "   ssh ${SERVER}"
echo "   cd ${BACKEND_DIR}"
echo "   python3 test_email.py"
echo ""
echo "4. Restart backend:"
echo "   sudo bash ${BACKEND_DIR}/restart_backend.sh"
echo ""
echo "5. Test on website:"
echo "   https://docdianasanchez.com"
echo ""
echo "📚 Full guide: backend/EMAIL_SETUP_GUIDE.md"
echo ""
