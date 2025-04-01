#!/bin/bash

# Script to clean up Docker volumes and containers for OpenCrawl

# Stop and remove containers
echo "=== Stopping and removing OpenCrawl containers ==="
docker-compose down -v

# Force remove containers if any still exist
echo -e "\n=== Force removing any lingering containers ==="
docker rm -f opencrawl-postgres opencrawl-zookeeper opencrawl-kafka 2>/dev/null || true

# Remove volumes (ignore errors if they don't exist)
echo -e "\n=== Removing Docker volumes ==="
docker volume rm opencrawl_postgres_data 2>/dev/null || true
echo "Note: It's normal to see 'Error: No such volume' messages if this is your first run."

# Prune all volumes that might be left behind
echo -e "\n=== Pruning dangling volumes ==="
docker volume prune -f

# Show current status
echo -e "\n=== Current Docker status ==="
docker ps -a | grep -E 'opencrawl|CONTAINER'

echo -e "\n=== Done! ==="
echo "You can now restart the services with: docker-compose up -d"
echo "To view logs: docker-compose logs -f" 