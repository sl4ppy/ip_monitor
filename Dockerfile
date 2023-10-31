# /mnt/data/Dockerfile

# Use a base image with Python installed
FROM python:3.8-slim

# Update package list and install cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

# Copy the script into the container
COPY ip_monitor.py /usr/src/app/ip_monitor.py

# Set up the CRON job to run the script every hour
RUN echo "0 * * * * python /usr/src/app/ip_monitor.py" | crontab -

# Install cron and requests library
RUN apt-get update && apt-get install -y cron && pip install requests && rm -rf /var/lib/apt/lists/*