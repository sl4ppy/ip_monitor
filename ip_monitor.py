# /mnt/data/ip_monitor.py

import os
import logging
import smtplib
import socket
from email.mime.text import MIMEText

# Configure logging to output to stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_public_ip():
    # Retrieve the public IP address by connecting to a remote server
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        current_ip = s.getsockname()[0]
        logging.info(f'Checked IP: {current_ip}')
    finally:
        s.close()
    return current_ip

def send_email(new_ip, previous_ip):
    # Compose the email
    subject = f"IP Address Changed: {new_ip}"
    body = f"Your IP address has changed from {previous_ip} to {new_ip}."
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = "ip-monitor@thevandorens.com"
    msg["To"] = "chris@thevandorens.com"

    # Send the email
    with smtplib.SMTP_SSL('smtp.fastmail.com', 465) as server:
        server.login(os.environ['SMTP_USERNAME'], os.environ['SMTP_PASSWORD'])
        server.send_message(msg)
        logging.info(f'Sent notification: IP changed from {previous_ip} to {new_ip}')

def monitor_ip():
    # Check the current IP and compare with the last known IP
    current_ip = get_public_ip()
    try:
        with open('/data/last_ip.txt', 'r') as file:
            last_ip = file.read().strip()
    except FileNotFoundError:
        last_ip = None

    # If the IP has changed, send a notification and update the last known IP
    if current_ip != last_ip:
        send_email(current_ip, last_ip)
        with open('/data/last_ip.txt', 'w') as file:
            file.write(current_ip)

if __name__ == '__main__':
    monitor_ip()
