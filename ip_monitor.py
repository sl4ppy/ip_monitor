# /mnt/data/ip_monitor.py

import argparse
import os
import dotenv
import logging
import smtplib
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Configure logging to output to stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

env_vars = dotenv.dotenv_values()  # Load environment variables into a dictionary

def get_public_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json')
        response.raise_for_status()  # Raise exception for failed requests
        current_ip = response.json()['ip']
        logging.info(f'Check returned IP: {current_ip}')
        return current_ip
    except requests.RequestException as e:
        logging.info(f'Failed to retrieve public IP: {e}')
        return None  # Return None if the request fails

def send_email(new_ip, previous_ip):
    email_recipient = env_vars.get('EMAIL_RECIPIENT')
    if not email_recipient:
        logging.error("EMAIL_RECIPIENT not found in .env file.")
        return  # Exit the function if the email recipient is not specified

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

    smtp_username = env_vars.get('SMTP_USERNAME')
    smtp_password = env_vars.get('SMTP_PASSWORD')
    
    # Send the email
    with smtplib.SMTP_SSL('smtp.fastmail.com', 465) as server:
        try:
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            logging.info(f'Sent notification: IP changed from {previous_ip} to {new_ip}')
        except smtplib.SMTPException as e:
            logging.info(f'Failed to send email: {e}')
            logging.info(f'Server response: {server.last_server_response}')

def monitor_ip(force_send=False):
    # Check the current IP and compare with the last known IP
    current_ip = get_public_ip()
    try:
        with open('/data/last_ip.txt', 'r') as file:
            last_ip = file.read().strip()
    except FileNotFoundError:
        last_ip = None

    # If the IP has changed or force_send is True, send a notification and update the last known IP
    if current_ip != last_ip or force_send:
        send_email(current_ip, last_ip)
        with open('/data/last_ip.txt', 'w') as file:
            file.write(current_ip)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-now', action='store_true', help='Run the script immediately and send email notification')
    args = parser.parse_args()

    if args.run_now:
        monitor_ip(force_send=True)  # Pass the force_send argument as True

if __name__ == '__main__':
    main()
