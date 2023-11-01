# Import required libraries
import os
import smtplib
import logging
import requests
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base
from apscheduler.schedulers.background import BackgroundScheduler

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

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
    engine = create_engine('sqlite:///ip_events.db')
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)

# Function to get IP data
def get_ip_data():
    try:
        response = requests.get('https://ipapi.co/json/')
        response.raise_for_status()
        data = response.json()
        print(data)  # Log the data to see its structure
        return data['ip'], data['city'], data['region'], data['country_name']
    except requests.RequestException as e:
        logging.error(f'Failed to retrieve IP data: {e}')
        return None, None, None, None


# Function to send email
def send_email(body, subject):
    msg = MIMEText(body, 'html')
    msg['Subject'] = subject
    msg['From'] = os.getenv('EMAIL_SENDER')
    msg['To'] = os.getenv('EMAIL_RECIPIENT')
    with smtplib.SMTP_SSL(os.getenv('SMTP_SERVER'), os.getenv('SMTP_PORT')) as server:
        server.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD'))
        server.send_message(msg)

# Function to generate report
def generate_report(start_date, end_date):
    Session = init_db()
    session = Session()
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
    current_ip, city, region, country = get_ip_data()
    try:
        with open('last_ip.txt', 'r') as file:
            last_ip = file.read().strip()
    except FileNotFoundError:
        last_ip = None
    if current_ip != last_ip:
        send_email(f'Your IP address has changed to {current_ip}', 'IP Address Changed')
        with open('last_ip.txt', 'w') as file:
            file.write(current_ip)
        Session = init_db()
        session = Session()
        event = IPChangeEvent(ip_address=current_ip, city=city, region=region, country=country)
        session.add(event)
        session.commit()

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

