# Use a base image with Python installed
FROM python:3.8-slim

# Update package list and install cron and necessary build tools
RUN apt-get update && apt-get install -y cron build-essential && rm -rf /var/lib/apt/lists/*

# Copy the script and other necessary files into the container
COPY ip_monitor.py /usr/src/app/ip_monitor.py
COPY config.yaml /usr/src/app/config.yaml
COPY email_template.html /usr/src/app/email_template.html
COPY ip_query_cli.py /usr/src/app/ip_query_cli.py

# Set up the CRON job to run the script every hour
RUN echo "0 * * * * python /usr/src/app/ip_monitor.py" | crontab -

# Install necessary Python libraries
RUN pip install requests python-dotenv sqlalchemy apscheduler pyyaml --root-user-action=ignore

# Keep the container running
CMD ["cron", "-f"]
