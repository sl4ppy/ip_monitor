# /mnt/data/ip_monitor.py

import sys
import os
import logging
import logging.handlers
import smtplib
import requests
import yaml
import jinja2  # Import the jinja2 library
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy import create_engine, Column, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# Load configurations from the file
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Configure logging based on configurations
log_config = config['logging']
logging.basicConfig(
    level=log_config['level'],
    format=log_config['format'],
    handlers=[
        logging.handlers.TimedRotatingFileHandler(
            log_config['file']['path'],
            when=log_config['file']['rotation']['when'],
            interval=log_config['file']['rotation']['interval'],
            backupCount=log_config['file']['rotation']['backupCount']
        ) if 'file' in log_config else logging.StreamHandler()
    ]
)


# Define the SQLAlchemy model
Base = declarative_base()
class IPChangeEvent(Base):
    __tablename__ = 'ip_change_events'
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=func.now())
    ip_address = Column(String)
    city = Column(String)
    region = Column(String)
    country = Column(String)

# Database initialization function
def init_db():
    engine = create_engine('sqlite:///ip_monitor.db')
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def get_geolocation(ip_address):
    try:
        response = requests.get(f'https://ipinfo.io/{ip_address}/json')
        response.raise_for_status()  # Raise exception for failed requests
        geolocation = response.json()
        logging.info(f'Geolocation data for {ip_address}: {geolocation}')
        return geolocation
    except requests.RequestException as e:
        logging.info(f'Failed to retrieve geolocation: {e}')
        return None  # Return None if the request fails

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
    email_to = os.getenv('EMAIL_TO').split(',')  # Split EMAIL_TO by comma to get a list of recipients
    email_from = os.getenv('EMAIL_FROM')
    smtp_config = config['smtp']
    geolocation = get_geolocation(new_ip)
    geolocation_info = f"{geolocation['city']}, {geolocation['region']}, {geolocation['country']}" if geolocation else 'Unknown'
    # Load and render the email template
    with open('email_template.html', 'r') as file:
        template = jinja2.Template(file.read())
    body = template.render(new_ip=new_ip, previous_ip=previous_ip, geolocation=geolocation_info)
    
    msg = MIMEMultipart('alternative')
    msg["Subject"] = 'IP Address Changed'
    msg["From"] = email_from
    
    msg.attach(MIMEText(body, 'html'))  # Attach the HTML content
    
    with smtplib.SMTP_SSL(smtp_config['server'], smtp_config['port']) as server:
        server.login(smtp_config['username'], smtp_config['password'])
        for recipient in email_to:
            msg['To'] = recipient  # Set the recipient in the message header
            server.send_message(msg)  # Send the email
            logging.info(f'Sent notification to {recipient}: IP changed from {previous_ip} to {new_ip}')

def monitor_ip(session, force_send=False):
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
        # Insert a new IP change event into the database
        event = IPChangeEvent(ip_address=current_ip, city=geolocation['city'],
                              region=geolocation['region'], country=geolocation['country'])
        session.add(event)
        session.commit()

if __name__ == '__main__':
    force_send = '--run-now' in sys.argv  # Check if --run-now is specified in the command-line arguments
    monitor_ip(force_send)
    Session = init_db()
    session = Session()
    monitor_ip(session, force_send)