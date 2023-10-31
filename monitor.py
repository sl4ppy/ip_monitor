# path/ip_monitor.py

import requests
import smtplib
from email.mime.text import MIMEText

# Function to get the current public IP address
def get_current_ip():
    response = requests.get('https://api.ipify.org')
    response.raise_for_status()
    return response.text.strip()

# Function to send an email notification
def send_email_notification(new_ip):
    msg = MIMEText(f'Your IP has changed to: {new_ip}')
    msg['Subject'] = 'IP Address Change Notification'
    msg['From'] = 'your_email@fastmail.com'
    msg['To'] = 'chris@thevandorens.com'

    with smtplib.SMTP('smtp.fastmail.com', 587) as server:
        server.starttls()
        server.login('your_email@fastmail.com', 'your_password')
        server.sendmail(msg['From'], [msg['To']], msg.as_string())

def main():
    try:
        # Get the current public IP
        current_ip = get_current_ip()

        # Read the last known IP from file
        try:
            with open('last_ip.txt', 'r') as file:
                last_ip = file.read().strip()
        except FileNotFoundError:
            last_ip = None

        # Compare and send a notification if the IP has changed
        if current_ip != last_ip:
            send_email_notification(current_ip)
            with open('last_ip.txt', 'w') as file:
                file.write(current_ip)
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    main()
