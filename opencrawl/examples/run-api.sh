#!/bin/bash

# Script to build and run the OpenCrawl API service

echo "=== Starting OpenCrawl API ==="

# Ensure we're in the examples directory
cd "$(dirname "$0")"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "Error: Docker is not running or not installed."
  echo "Please start Docker and try again."
  exit 1
fi

# Stop any existing containers
echo "Stopping any existing OpenCrawl containers..."
docker-compose down

# Build and start the services
echo "Building and starting OpenCrawl API services..."
docker-compose up -d --build

# Show running containers
echo -e "\n=== OpenCrawl API services are running ==="
docker-compose ps

echo -e "\n=== API is available at http://localhost:8000 ==="
echo "Try these endpoints:"
echo "  - GET  http://localhost:8000/         (API info)"
echo "  - GET  http://localhost:8000/health   (Health check)"
echo "  - POST http://localhost:8000/crawl    (Crawl websites)"
echo -e "\nExample crawl request:"
echo '{
  "urls": ["https://example.com", "https://news.ycombinator.com"],
  "user_id": "optional-user-id",
  "thread_id": "optional-thread-id"
}'

echo -e "\nTo view logs: docker-compose logs -f api"
echo "To stop the service: docker-compose down" 