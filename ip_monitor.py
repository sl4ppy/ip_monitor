# /mnt/data/ip_monitor.py

import smtplib
import socket
from email.mime.text import MIMEText

def get_public_ip():
    # Obtain the current public IP by connecting to a remote server
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]

def send_email(new_ip, previous_ip):
    # Prepare the email content
    msg = MIMEText(f'Your IP has changed from {previous_ip} to {new_ip}.')
    msg['Subject'] = 'IP Address Changed'
    msg['From'] = 'notify@thevandorens.com'
    msg['To'] = 'chris@thevandorens.com'

    # Send the email via Fastmail's SMTP server
        with smtplib.SMTP_SSL('smtp.fastmail.com', 465) as server:
            server.login(os.environ['SMTP_USERNAME'], os.environ['SMTP_PASSWORD'])  # Use environment variables
        server.send_message(msg)

def monitor_ip():
    # Load the last known IP from a file
    try:
        with open('/data/last_ip.txt', 'r') as file:
            last_ip = file.read().strip()
    except FileNotFoundError:
        last_ip = ''

    # Get the current public IP
    current_ip = get_public_ip()

    # If the IP has changed, send an email and update the last known IP
    if current_ip != last_ip:
        send_email(current_ip, last_ip)
        with open('/data/last_ip.txt', 'w') as file:
            file.write(current_ip)

# Entry point for the script
if __name__ == '__main__':
    monitor_ip()
