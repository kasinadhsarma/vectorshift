#!/bin/bash

# Start Redis if not running
redis-server &

# Start backend
cd backend
uvicorn main:app --reload --port 8000 &

# Start frontend
cd ..
npm run dev