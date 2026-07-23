#!/bin/bash
# Script to reload the Diana booking backend server
# Run this on the server: ssh beckham23@192.168.0.131 "bash /home/beckham23/diana-booking-backend/reload_server.sh"

cd /home/beckham23/diana-booking-backend

echo "Reloading Gunicorn..."
sudo kill -HUP $(pgrep -f "gunicorn.*app:app" | head -1)

if [ $? -eq 0 ]; then
    echo "✓ Server reloaded successfully"
    echo "Visit: https://api.docdianasanchez.com/admin/view"
else
    echo "✗ Failed to reload. Try:"
    echo "  sudo systemctl restart diana-booking-backend"
fi
