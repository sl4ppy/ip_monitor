# /mnt/data/ip_monitor.py

import sys
import os
import dotenv
import logging
import smtplib
import argparse
import requests  # Import the requests library here
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
    # Retrieve the email recipient from the .env file
    email_recipient = dotenv.dotenv_values().get('EMAIL_RECIPIENT')
    if not email_recipient:
        logging.error("EMAIL_RECIPIENT not found in .env file.")
        return  # Exit the function if the email recipient is not specified

    # Compose the email
    
    # Create a MIMEText object for the HTML content
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background-color: #ffffff; padding: 20px; border-radius: 8px; text-align: center;">
                <h1 style="color: #333333;">IP Address Changed</h1>
                <p style="color: #666666; font-size: 18px;">Your IP address has changed.</p>
                <p style="color: #666666; font-size: 18px;">Previous IP: <strong>{previous_ip}</strong></p>
                <p style="color: #666666; font-size: 18px;">New IP: <strong>{new_ip}</strong></p>
            </div>
        </body>
    </html>
    """
    msg = MIMEMultipart("alternative")
    msg.attach(MIMEText(html_content, 'html'))

    msg["Subject"] = f"IP Address Changed: {new_ip}"
    msg["From"] = "ip-monitor@thevandorens.com"
    msg["To"] = email_recipient

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
    if current_ip != last_ip:
        send_email(current_ip, last_ip)
        with open('/data/last_ip.txt', 'w') as file:
            file.write(current_ip)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-now', action='store_true', help='Run the script immediately')
    args = parser.parse_args()

    if args.run_now:
        monitor_ip()

if __name__ == '__main__':
    main()
