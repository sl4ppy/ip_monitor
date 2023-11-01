#!/bin/bash

# Pull the latest
#git pull

# Build the Docker image
docker-compose build

# Stop any running containers
docker-compose down

# Deploy the updated container
docker-compose up -d
