#!/bin/bash

# Check if Redis is running
redis-cli ping > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Starting Redis server..."
    redis-server &
    sleep 2
fi

# Start backend
echo "Starting backend server..."
cd backend
source .env.sh
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload &

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 5

# Start frontend
echo "Starting frontend server..."
cd ..
npm install --legacy-peer-deps
npm run dev
