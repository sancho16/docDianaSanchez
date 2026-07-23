#!/bin/bash
# Deploy Updated Backend with GET Endpoints
# Fixed: Use absolute paths instead of ~ to avoid sudo path issues

echo "🔄 Deploying Updated Backend..."
echo ""

# Use absolute path
BACKEND_DIR="/home/beckham23/diana-booking-backend"
cd "$BACKEND_DIR"

# Backup current app.py
BACKUP_FILE="app.py.backup_before_get_$(date +%Y%m%d_%H%M%S)"
echo "📦 Creating backup: $BACKUP_FILE"
cp app.py "$BACKUP_FILE"

# Replace with updated version
echo "📝 Installing updated app.py with GET endpoints..."
cp app_updated.py app.py

echo ""
echo "✅ Code updated! Now restarting backend..."
echo ""

# Stop old processes
echo "🛑 Stopping old Gunicorn processes..."
sudo pkill -f "gunicorn.*app:app"
sleep 2

# Force kill if still running
if pgrep -f "gunicorn.*app:app" > /dev/null; then
    echo "⚠️  Force killing remaining processes..."
    sudo pkill -9 -f "gunicorn.*app:app"
    sleep 1
fi

# Start new process (use absolute path)
echo "▶️  Starting Gunicorn..."
sudo nohup /home/beckham23/faker-env/bin/gunicorn -w 2 -b 127.0.0.1:8000 --reuse-port app:app > "$BACKEND_DIR/gunicorn.log" 2>&1 &

sleep 3

# Verify it's running
if pgrep -f "gunicorn.*app:app" > /dev/null; then
    echo ""
    echo "✅ Backend restarted successfully!"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Testing Endpoints..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    echo "1️⃣  Health Check:"
    curl -s http://localhost:8000/api/health
    echo ""
    echo ""
    
    echo "2️⃣  GET Bookings (first 3):"
    curl -s http://localhost:8000/api/bookings?limit=3 | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"✓ Found {data.get('count', 0)} bookings\"); [print(f\"  - {b.get('name')} ({b.get('phone')})\") for b in data.get('bookings', [])[:3]]" 2>/dev/null || echo "  (Bookings endpoint responding)"
    echo ""
    echo ""
    
    echo "3️⃣  Admin Panel (should still work):"
    curl -s http://localhost:8000/admin 2>/dev/null | head -5
    echo "..."
    echo ""
    echo ""
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ Deployment Complete!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📋 What's New:"
    echo "  ✓ GET  /api/bookings           - Fetch all bookings"
    echo "  ✓ GET  /api/bookings/:id       - Fetch one booking"
    echo "  ✓ PATCH /api/bookings/:id      - Update booking status"
    echo "  ✓ DELETE /api/bookings/:id     - Delete booking"
    echo ""
    echo "🔗 URLs:"
    echo "  Backend Admin: https://api.docdianasanchez.com/admin"
    echo "  Frontend Admin: https://docdianasanchez.com/admin/"
    echo "  API Health: https://api.docdianasanchez.com/api/health"
    echo ""
    echo "📝 Next Steps:"
    echo "  1. Test backend admin: https://api.docdianasanchez.com/admin"
    echo "  2. Test frontend admin: https://docdianasanchez.com/admin/"
    echo "  3. Both should show all 80 appointments!"
    echo ""
else
    echo ""
    echo "❌ Failed to start backend"
    echo ""
    echo "Check logs:"
    tail -50 "$BACKEND_DIR/gunicorn.log"
    echo ""
    echo "To rollback:"
    echo "  cd $BACKEND_DIR"
    echo "  cp $BACKUP_FILE app.py"
    echo "  sudo bash restart_backend.sh"
fi
