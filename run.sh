#!/bin/bash

# Set up virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Setting up Python virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Start backend server in background
echo "Starting backend server..."
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Navigate to client directory
cd client

# Install npm dependencies
echo "Installing frontend dependencies..."
npm install

# Start frontend server
echo "Starting frontend server..."
npm start

# Cleanup function
cleanup() {
    echo "Shutting down servers..."
    kill $BACKEND_PID
    exit
}

# Set up trap for SIGINT (Ctrl+C)
trap cleanup SIGINT

# Wait for frontend to exit
wait 