# /mnt/data/ip_monitor.py

import sys
import os
import dotenv
import logging
import smtplib
import requests  # Import the requests library here
from email.mime.text import MIMEText

# Configure logging to output to stdout
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(), logging.FileHandler('/var/log/ip_monitor.log')])


dotenv.load_dotenv()

def get_public_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json')
        response.raise_for_status()  # Raise exception for failed requests
        current_ip = response.json()['ip']
        logging.info(f'Check returned IP: {current_ip}')
        return current_ip
    except requests.RequestException as e:
        logging.exception(f'Failed to retrieve public IP: {e}')
        return None  # Return None if the request fails

def send_email(new_ip, previous_ip):
    # Compose the email
    subject = f"IP Address Changed: {new_ip}"
    body = f"Your IP address has changed from {previous_ip} to {new_ip}."
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = "ip-monitor@thevandorens.com"
    msg["To"] = "chris@thevandorens.com"

    try:
        smtp_username = dotenv.dotenv_values().get('SMTP_USERNAME')  # Modified
        smtp_password = dotenv.dotenv_values().get('SMTP_PASSWORD')  # Modified
        logging.info(f'Found .env var: {smtp_username}')
    except smtplib.SMTPException as e:
        logging.exception(f'Failed to send email: {e}')
        return  # Exit the function if the environment variables are missing

    # Send the email
    with smtplib.SMTP_SSL('smtp.fastmail.com', 465) as server:
        try:
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            logging.info(f'Sent notification: IP changed from {previous_ip} to {new_ip}')
        except smtplib.SMTPException as e:
            logging.info(f'Failed to send email: {e}')
            logging.info(f'Server response: {server.last_server_response}')

def monitor_ip():
    # Check the current IP and compare with the last known IP
    current_ip = get_public_ip()
    try:
        with open('/data/last_ip.txt', 'r') as file:
            last_ip = file.read().strip()
            logging.info(f'Updated IP to {current_ip}')
    except FileNotFoundError:
        last_ip = None

    # If the IP has changed, send a notification and update the last known IP
    if current_ip != last_ip  or len(sys.argv) > 1:
        send_email(current_ip, last_ip)
        with open('/data/last_ip.txt', 'w') as file:
            file.write(current_ip)

if __name__ == '__main__':
    monitor_ip()
