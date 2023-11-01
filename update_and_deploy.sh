#!/bin/bash

# Pull the latest
#git pull

# Navigate to project directory
cd ~/github/ip_monitor

# Build the Docker image
docker-compose build

# Stop any running containers
docker-compose down

# Deploy the updated container
docker-compose up -d
