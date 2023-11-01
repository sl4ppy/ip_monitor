# /mnt/data/Dockerfile

# Use a base image with Python installed
FROM python:3.8-slim

# Update package list, install cron, and install necessary Python libraries
RUN apt-get update && \
    apt-get install -y cron && \
    pip install requests python-dotenv && \
    rm -rf /var/lib/apt/lists/*

# Copy the script and the .env file into the container
COPY ip_monitor.py .env /usr/src/app/

# Set up the CRON job to run the script every hour and log output
RUN echo "0 * * * * python /usr/src/app/ip_monitor.py >> /var/log/cron.log 2>&1" | crontab -

# Optional: Create a symbolic link to make the log file accessible from outside the container
RUN ln -s /var/log/ip_monitor.log /usr/src/app/ip_monitor.log

# Command to keep the container running and start cron in the foreground
CMD ["cron", "-f"]
