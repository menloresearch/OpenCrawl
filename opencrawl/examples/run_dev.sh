#!/bin/bash

# Make sure we're in the correct directory
cd "$(dirname "$0")"

# Start the FastAPI backend
echo "Starting FastAPI backend..."
python api.py &
BACKEND_PID=$!

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    echo "Error: frontend directory not found!"
    echo "Expected location: $(pwd)/frontend"
    kill $BACKEND_PID
    exit 1
fi

# Change to the frontend directory and start it
echo "Starting Next.js frontend..."
cd frontend && npm run dev &
FRONTEND_PID=$!

# Function to kill both processes on exit
cleanup() {
    echo "Shutting down services..."
    kill $BACKEND_PID
    kill $FRONTEND_PID
    exit
}

# Register the cleanup function for when the script is terminated
trap cleanup INT TERM

echo "Development environment is running!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "Press Ctrl+C to stop both services."

# Wait forever (until Ctrl+C)
wait 