# path/Dockerfile

# Use a lightweight Python image
FROM python:3.9-slim

# Install necessary Python packages
RUN pip install requests

# Copy the script into the container
COPY ip_monitor.py /ip_monitor.py

# Command to run the script
CMD ["python", "/ip_monitor.py"]
