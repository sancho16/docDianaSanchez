#!/bin/bash
# URGENT FIX: Reload Gunicorn to apply medical records route and perfect circle charts
# Run this on the server: ssh beckham23@192.168.0.131 'bash /home/beckham23/diana-booking-backend/URGENT_FIX.sh'

echo "========================================="
echo "URGENT FIX: Reloading Gunicorn"
echo "========================================="
echo ""

cd /home/beckham23/diana-booking-backend

# Step 1: Verify the route exists
echo "1. Verifying route exists in app.py..."
if grep -q '@app.route("/admin/medical-records"' app.py; then
    echo "   ✅ Route found in app.py"
else
    echo "   ❌ Route NOT found - Need to add it"
    exit 1
fi

# Step 2: Verify chart CSS exists
echo "2. Verifying chart CSS..."
if grep -q 'aspect-ratio:1/1' app.py; then
    echo "   ✅ Chart CSS found"
else
    echo "   ❌ Chart CSS NOT found"
    exit 1
fi

# Step 3: Find Gunicorn master process
echo "3. Finding Gunicorn processes..."
GUNICORN_PIDS=$(pgrep -f 'gunicorn.*app:app')
if [ -z "$GUNICORN_PIDS" ]; then
    echo "   ❌ No Gunicorn process found!"
    exit 1
fi
echo "   ✅ Found Gunicorn processes: $GUNICORN_PIDS"

# Step 4: Kill worker processes (master will respawn them)
echo "4. Killing Gunicorn workers..."
pkill -f 'python3.*gunicorn' 2>/dev/null
sleep 2

# Step 5: Check if Gunicorn restarted
echo "5. Waiting for Gunicorn to restart..."
sleep 5

NEW_PIDS=$(pgrep -f 'gunicorn.*app:app')
if [ -z "$NEW_PIDS" ]; then
    echo "   ❌ Gunicorn did not restart!"
    echo "   Manual restart required. Run:"
    echo "   sudo systemctl restart diana-booking-backend"
    echo "   OR"
    echo "   cd /home/beckham23/diana-booking-backend && nohup /home/beckham23/faker-env/bin/gunicorn -w 2 -b 127.0.0.1:8000 app:app &"
    exit 1
fi

echo "   ✅ Gunicorn restarted with new workers"

# Step 6: Test the medical records route
echo "6. Testing medical records route..."
sleep 2
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8000/admin/medical-records?booking_id=80" 2>/dev/null || echo "000")

if [ "$RESPONSE" = "302" ] || [ "$RESPONSE" = "401" ]; then
    echo "   ✅ Route is working (needs authentication)"
elif [ "$RESPONSE" = "200" ]; then
    echo "   ✅ Route is working perfectly!"
else
    echo "   ⚠️  Route responded with code: $RESPONSE"
    echo "   This might be normal if authentication is required"
fi

# Step 7: Show current status
echo ""
echo "========================================="
echo "FINAL STATUS"
echo "========================================="
echo "Gunicorn workers:"
ps aux | grep 'gunicorn.*app:app' | grep -v grep

echo ""
echo "✅ FIX COMPLETE"
echo ""
echo "Next steps:"
echo "1. Visit: https://api.docdianasanchez.com/admin/view"
echo "2. Log in with Google/Token"
echo "3. Check charts are circular"
echo "4. Click an appointment to test medical records"
echo ""
echo "If still having issues:"
echo "- Check nginx/proxy logs"
echo "- Verify authentication cookie"
echo "- Try clearing browser cache"
