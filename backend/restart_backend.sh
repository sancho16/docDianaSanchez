#!/bin/bash
# Restart Backend Script
# Run with: sudo bash restart_backend.sh

echo "🔄 Restarting Dr. Diana Sánchez Backend API..."

# Stop old processes
echo "Stopping old Gunicorn processes..."
pkill -f "gunicorn.*app:app"
sleep 2

# Verify they're stopped
if pgrep -f "gunicorn.*app:app" > /dev/null; then
    echo "⚠️  Force killing remaining processes..."
    pkill -9 -f "gunicorn.*app:app"
    sleep 1
fi

# Start new process
cd /home/beckham23/diana-booking-backend

echo "Starting new Gunicorn server..."
nohup /home/beckham23/faker-env/bin/gunicorn -w 2 -b 127.0.0.1:8000 --reuse-port app:app > gunicorn.log 2>&1 &

sleep 3

# Check if it's running
if pgrep -f "gunicorn.*app:app" > /dev/null; then
    echo "✅ Backend restarted successfully!"
    echo ""
    echo "Testing API..."
    curl -s http://localhost:8000/api/health
    echo ""
    echo ""
    echo "Checking bookings endpoint..."
    curl -s http://localhost:8000/api/bookings | head -200
    echo ""
else
    echo "❌ Failed to start backend"
    echo "Check logs: tail -50 /home/beckham23/diana-booking-backend/gunicorn.log"
fi
