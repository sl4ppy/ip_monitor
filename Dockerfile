# Use a base image with Python installed
FROM python:3.8-slim

# Update package list and install cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

# Copy the script into the container
COPY ip_monitor.py /usr/src/app/ip_monitor.py

# Copy the .env file into the image
COPY .env /usr/src/app/.env

# Set up the CRON job to run the script every hour
RUN echo "0 * * * * python /usr/src/app/ip_monitor.py" | crontab -

# Install necessary Python libraries
RUN pip install requests python-dotenv sqlalchemy

# This command will keep the container running and allow cron to execute the script
CMD ["cron", "-f"]
