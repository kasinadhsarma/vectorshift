#!/bin/bash

echo "Starting VectorShift development environment..."

# Function to check if a port is in use
check_port() {
    lsof -i :$1 > /dev/null 2>&1
    return $?
}

# Function to check if a service is ready
wait_for_service() {
    local port=$1
    local service=$2
    local max_attempts=30
    local attempt=1

    echo "Waiting for $service to be ready..."
    while ! check_port $port; do
        if [ $attempt -ge $max_attempts ]; then
            echo "$service failed to start after $max_attempts attempts"
            return 1
        fi
        echo "Attempt $attempt: $service not ready, waiting..."
        sleep 2
        ((attempt++))
    done
    echo "$service is ready!"
    return 0
}

# Setup environment variables
setup_environment() {
    echo "Checking environment setup..."
    if [ ! -f "backend/.env" ]; then
        if [ ! -f "backend/.env.example" ]; then
            echo "Error: backend/.env.example not found"
            exit 1
        fi
        echo "Creating .env file from example..."
        cp backend/.env.example backend/.env
        echo "Please update backend/.env with your actual configuration values"
        echo "Press any key to open .env file for editing..."
        read -n 1
        if command -v code &> /dev/null; then
            code backend/.env
        else
            ${EDITOR:-vi} backend/.env
        fi
    fi
}

# Initialize database
initialize_database() {
    echo "Initializing database..."
    cd backend
    source venv/bin/activate
    echo "Running database initialization script..."
    python init_db.py
    if [ $? -ne 0 ]; then
        echo "Database initialization failed. Please check the error messages above."
        exit 1
    fi
    echo "Database initialization completed successfully."
    cd ..
}

# Initialize backend
setup_backend() {
    echo "Setting up backend..."
    cd backend
    if [ ! -d "venv" ]; then
        echo "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    source venv/bin/activate
    echo "Installing backend dependencies..."
    pip install -r requirements.txt

    # Check if env variables are properly set
    if ! python -c "import os; assert all(v for v in [os.getenv('NOTION_CLIENT_ID'), os.getenv('NOTION_CLIENT_SECRET'), os.getenv('NOTION_REDIRECT_URI')])"; then
        echo "Error: Required environment variables are missing. Please update backend/.env"
        exit 1
    fi

    cd ..
}

# Setup environment first
setup_environment

# Start Redis if not running
if ! check_port 6379; then
    echo "Starting Redis..."
    redis-server &
    if ! wait_for_service 6379 "Redis"; then
        echo "Failed to start Redis. Please check if Redis is installed correctly."
        exit 1
    fi
else
    echo "Redis is already running"
fi

# Start Cassandra if not running
if ! check_port 9042; then
    echo "Starting Cassandra..."
    cassandra -f &
    if ! wait_for_service 9042 "Cassandra"; then
        echo "Failed to start Cassandra. Please check if Cassandra is installed correctly."
        exit 1
    fi
else
    echo "Cassandra is already running"
fi

# Wait for Cassandra to be fully ready
echo "Waiting for Cassandra to be fully ready..."
sleep 10

# Setup backend and initialize database
setup_backend
initialize_database

# Start backend service
echo "Starting backend service..."
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000 &

# Wait for backend to be ready
if ! wait_for_service 8000 "Backend"; then
    echo "Failed to start backend service. Please check the error messages above."
    exit 1
fi

# Initialize frontend
echo "Setting up frontend..."
cd ..
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

echo "Starting frontend service..."
npm run dev &

# Wait for frontend to be ready
if ! wait_for_service 3000 "Frontend"; then
    echo "Failed to start frontend service. Please check the error messages above."
    exit 1
fi

echo "Development environment is ready!"
echo "Services available at:"
echo "- Frontend: http://localhost:3000"
echo "- Backend: http://localhost:8000"
echo "- Redis: localhost:6379"
echo "- Cassandra: localhost:9042"
echo
echo "Health check endpoint: http://localhost:8000/health"
echo "API documentation: http://localhost:8000/docs"
echo
echo "Press Ctrl+C to stop all services"

# Keep script running and show logs
wait
