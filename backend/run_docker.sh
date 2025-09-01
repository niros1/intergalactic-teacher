#!/bin/bash

# Build and start the API server
echo "Building and starting API server..."
docker-compose up --build -d api

echo "Waiting for API to start..."
sleep 10

# Check if API is running
echo "Checking API status..."
curl -f http://localhost:8000/health || echo "API not ready yet"

echo "Running story generation tests..."
python3 test_story_api.py