#!/bin/bash

# Development setup script for OpenCrawl

echo "=== Setting up OpenCrawl development environment ==="

# Install the package in development mode
echo -e "\n=== Installing OpenCrawl in development mode ==="
pip install -e .

# Verify installation
echo -e "\n=== Verifying installation ==="
python -c "from opencrawl import OpenCrawl; print('OpenCrawl library installed successfully!')"

# Clean up Docker environment
echo -e "\n=== Cleaning up Docker environment ==="
./docker-cleanup.sh

# Start Docker services
echo -e "\n=== Starting Docker services ==="
docker-compose up -d

echo -e "\n=== Setup complete! ==="
echo "You can now run the demo with: ./run-demo.sh" 