# Import required libraries
import sys
import os
import smtplib
import logging
import requests
import time
from string import Template
from pathlib import Path
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.message import EmailMessage
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from apscheduler.schedulers.background import BackgroundScheduler

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

MAX_RETRIES = 5
BACKOFF_FACTOR = 2

# Configure logging
logging.basicConfig(level=logging.DEBUG)


# Global session factory
SessionFactory = None

# Database setup
Base = declarative_base()

class IPChangeEvent(Base):
    __tablename__ = 'ip_change_events'
    id = Column(Integer, primary_key=True)
    ip_address = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    city = Column(String)
    region = Column(String)
    country = Column(String)

# Function to initialize the database
def init_db():
    global SessionFactory
    if SessionFactory is None:
        engine = create_engine('sqlite:///ip_events.db')
        Base.metadata.create_all(engine)
        SessionFactory = sessionmaker(bind=engine)

def get_session():
    if SessionFactory is None:
        init_db()
    return SessionFactory()

# Function to get IP data
def get_ip_data():
    url = 'https://ipapi.co/json/'
    headers = {
        "User-Agent": "IP Monitor (your_email@example.com)"  # Identify your app in the User-Agent string
    }
    for attempt in range(MAX_RETRIES):
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data['ip'], data['city'], data['region'], data['country_name']
        elif response.status_code == 429:
            # Rate limit exceeded, wait for the duration of the TTL before retrying
            ttl = int(response.headers.get('X-Ttl', 60))  # Default to 60 seconds if X-Ttl header is missing
            logging.info(f"Rate limit exceeded. Retrying in {ttl} seconds.")
            time.sleep(ttl)
        else:
            # Other HTTP error, wait for a short period before retrying
            logging.error(f"Failed to retrieve IP data: {response.status_code} {response.text}")
            wait_time = BACKOFF_FACTOR ** attempt
            logging.info(f"Retrying in {wait_time} seconds.")
            time.sleep(wait_time)
    logging.error(f"Failed to retrieve IP data after {MAX_RETRIES} attempts.")
    return None


# Function to send email
def send_email(message, subject, previous_ip, new_ip):
    with smtplib.SMTP_SSL(os.getenv('SMTP_SERVER'), os.getenv('SMTP_PORT')) as server:
        server.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD'))
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = os.getenv('EMAIL_SENDER')
        msg['To'] = os.getenv('EMAIL_RECIPIENT')

        # Load and format the HTML template
        template_path = Path(__file__).parent / 'email_template.html'
        html_template = template_path.read_text()

        # Replace tokens using the correct format
        formatted_html = html_template.replace("{{ previous_ip }}", str(previous_ip)).replace("{{ new_ip }}", str(new_ip))

        msg.add_alternative(formatted_html, subtype='html')
        server.send_message(msg)


# Function to generate report
def generate_report(start_date, end_date):
    session = get_session()
    try:
        events = session.query(IPChangeEvent).filter(
            IPChangeEvent.timestamp >= start_date,
            IPChangeEvent.timestamp <= end_date
        ).all()
        table = """
            <table border="1">
                <tr>
                    <th>Timestamp</th>
                    <th>IP Address</th>
                    <th>City</th>
                    <th>Region</th>
                    <th>Country</th>
                </tr>
        """
    finally:
        session.close()

    for event in events:
        table += f"""
            <tr>
                <td>{event.timestamp}</td>
                <td>{event.ip_address}</td>
                <td>{event.city}</td>
                <td>{event.region}</td>
                <td>{event.country}</td>
            </tr>
        """
    table += "</table>"
    return table

# Function to send scheduled report
def scheduled_report():
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    report = generate_report(start_date, end_date)
    body = f"""
        <html>
            <body>
                <h1>IP Change Report</h1>
                <p>The following table lists all IP change events from {start_date} to {end_date}:</p>
                {report}
            </body>
        </html>
    """
    send_email(body, 'Weekly IP Change Report')

# Function to start the scheduler
def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_report, 'cron', day_of_week='mon', hour=9, minute=0)
    scheduler.start()

# Function to monitor IP
def monitor_ip():
    ip_data = get_ip_data()
    if ip_data is None:
        logging.error("Failed to get IP data.")
        return  # Exit the function early
    current_ip, city, region, country = ip_data
    
    try:
        with open('last_ip.txt', 'r') as file:
            last_ip = file.read().strip()
    except FileNotFoundError:
        last_ip = None
    
    if current_ip != last_ip:
        send_email(f'Your IP address has changed from {last_ip} to {current_ip}', 'IP Address Changed', last_ip, current_ip)
        with open('last_ip.txt', 'w') as file:
            file.write(current_ip)
        
        session = get_session()
        try:
            event = IPChangeEvent(ip_address=current_ip, city=city, region=region, country=country)
            session.add(event)
            session.commit()
        finally:
            session.close()


# Main block
if __name__ == '__main__':
    if '--run-now' in sys.argv:
        monitor_ip()
    else:
        scheduler = BackgroundScheduler()
        scheduler.add_job(monitor_ip, 'interval', minutes=config['ip_check']['interval'])
        scheduler.start()

        # Shut down the scheduler when exiting the app
        atexit.register(lambda: scheduler.shutdown())