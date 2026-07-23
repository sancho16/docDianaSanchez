#!/bin/bash
# Verification script for admin view updates

echo "🔍 Verifying Admin View Updates..."
echo "=================================="
echo ""

# Check if changes are in the file
echo "1. Checking for perfect circle CSS..."
ssh beckham23@192.168.0.131 "grep -q 'aspect-ratio:1/1' /home/beckham23/diana-booking-backend/app.py" && \
  echo "   ✅ Perfect circle CSS found" || \
  echo "   ❌ Perfect circle CSS missing"

echo ""
echo "2. Checking for clickable row function..."
ssh beckham23@192.168.0.131 "grep -q 'function openMedicalRecord' /home/beckham23/diana-booking-backend/app.py" && \
  echo "   ✅ OpenMedicalRecord function found" || \
  echo "   ❌ OpenMedicalRecord function missing"

echo ""
echo "3. Checking for onclick handlers..."
ssh beckham23@192.168.0.131 "grep -q 'onclick=\"openMedicalRecord' /home/beckham23/diana-booking-backend/app.py" && \
  echo "   ✅ Onclick handlers found" || \
  echo "   ❌ Onclick handlers missing"

echo ""
echo "4. Checking Gunicorn process..."
ssh beckham23@192.168.0.131 "pgrep -f 'gunicorn.*app:app' > /dev/null" && \
  echo "   ✅ Gunicorn is running" || \
  echo "   ❌ Gunicorn is not running"

echo ""
echo "5. Checking if backup exists..."
BACKUP_COUNT=$(ssh beckham23@192.168.0.131 "ls /home/beckham23/diana-booking-backend/app.py.backup-* 2>/dev/null | wc -l")
if [ "$BACKUP_COUNT" -gt 0 ]; then
  echo "   ✅ Found $BACKUP_COUNT backup(s)"
else
  echo "   ⚠️  No backups found"
fi

echo ""
echo "=================================="
echo "📊 Verification Complete"
echo ""
echo "Next steps:"
echo "1. Visit: https://api.docdianasanchez.com/admin/view"
echo "2. Verify charts are perfect circles"
echo "3. Click on appointment rows to test medical records"
echo ""
echo "To reload server manually:"
echo "  ssh beckham23@192.168.0.131 'bash /home/beckham23/diana-booking-backend/reload_server.sh'"
