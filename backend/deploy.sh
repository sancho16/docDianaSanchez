#!/bin/bash

# Deployment script for Dr. Diana Sánchez Backend API
# Usage: ./deploy.sh [production|staging]

ENVIRONMENT=${1:-production}

echo "🚀 Deploying backend to $ENVIRONMENT..."

# Configuration
if [ "$ENVIRONMENT" = "staging" ]; then
    PORT=8001
    DB_NAME="diana_bookings_staging"
else
    PORT=8000
    DB_NAME="diana_bookings"
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on server
if [ ! -f "/home/beckham23/.ssh/authorized_keys" ]; then
    echo -e "${YELLOW}⚠️  This script should be run on the server (192.168.0.131)${NC}"
    echo "To deploy, run:"
    echo "  scp -r backend/* beckham23@192.168.0.131:~/diana-booking-backend/"
    echo "  ssh beckham23@192.168.0.131 'cd ~/diana-booking-backend && ./deploy.sh $ENVIRONMENT'"
    exit 0
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt --quiet

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo "Please create .env from .env.example and configure your database credentials"
    exit 1
fi

# Test database connection
echo "🔌 Testing database connection..."
python3 -c "
from dotenv import load_dotenv
import mysql.connector
import os
load_dotenv()
try:
    conn = mysql.connector.connect(
        host=os.getenv('DATABASE_HOST'),
        user=os.getenv('DATABASE_USER'),
        password=os.getenv('DATABASE_PASSWORD'),
        database=os.getenv('DATABASE_NAME')
    )
    print('✅ Database connection successful')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Database connection test failed${NC}"
    exit 1
fi

# Stop existing process
echo "🛑 Stopping existing backend process..."
pkill -f "python3 app.py" || true

# Start new process
echo "▶️  Starting backend server on port $PORT..."
nohup python3 app.py > backend_${ENVIRONMENT}.log 2>&1 &
PID=$!

# Wait a moment for the server to start
sleep 2

# Check if process is running
if ps -p $PID > /dev/null; then
    echo -e "${GREEN}✅ Backend server started successfully (PID: $PID)${NC}"
    echo "📋 Log file: backend_${ENVIRONMENT}.log"
    echo "🌐 API URL: http://192.168.0.131:$PORT"
    echo ""
    echo "To check logs: tail -f backend_${ENVIRONMENT}.log"
    echo "To stop server: pkill -f 'python3 app.py'"
else
    echo -e "${RED}❌ Failed to start backend server${NC}"
    echo "Check logs: cat backend_${ENVIRONMENT}.log"
    exit 1
fi

# Test API health endpoint
sleep 1
echo "🏥 Testing API health..."
curl -s http://localhost:$PORT/api/health | python3 -m json.tool || echo -e "${YELLOW}⚠️  Health check failed (this might be normal if starting)${NC}"

echo ""
echo -e "${GREEN}🎉 Deployment complete!${NC}"
