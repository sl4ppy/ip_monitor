# /mnt/data/ip_query_cli.py

import argparse
import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ip_monitor import IPChangeEvent, init_db  # Import the model and init_db function from ip_monitor.py

def list_recent_changes(session, limit):
    # Query the database for recent IP changes
    for event in session.query(IPChangeEvent).order_by(IPChangeEvent.timestamp.desc()).limit(limit):
        print(f"{event.timestamp}: {event.ip_address} (Location: {event.city}, {event.region}, {event.country})")

def search_ip(session, ip_address):
    # Query the database for occurrences of a specific IP
    for event in session.query(IPChangeEvent).filter(IPChangeEvent.ip_address == ip_address).order_by(IPChangeEvent.timestamp.desc()):
        print(f"{event.timestamp}: {event.ip_address} (Location: {event.city}, {event.region}, {event.country})")

def summary_report(session):
    # Generate a summary report of IP changes
    total_changes = session.query(IPChangeEvent).count()
    unique_ips = session.query(IPChangeEvent.ip_address).distinct().count()
    print(f"Total IP changes: {total_changes}")
    print(f"Unique IPs: {unique_ips}")

def main():
    parser = argparse.ArgumentParser(description="IP Monitor Query CLI")
    subparsers = parser.add_subparsers(dest='command', help='sub-command help')

    # Sub-command to list recent IP changes
    parser_recent = subparsers.add_parser('recent', help='List recent IP changes')
    parser_recent.add_argument('--limit', type=int, default=10, help='Limit the number of entries displayed')

    # Sub-command to search for an IP
    parser_search = subparsers.add_parser('search', help='Search for an IP address')
    parser_search.add_argument('ip', help='The IP address to search for')

    # Sub-command to generate a summary report
    parser_summary = subparsers.add_parser('summary', help='Generate a summary report')

    args = parser.parse_args()

    # Initialize the database
    Session = init_db()
    session = Session()

    # Execute the appropriate command
    if args.command == 'recent':
        list_recent_changes(session, args.limit)
    elif args.command == 'search':
        search_ip(session, args.ip)
    elif args.command == 'summary':
        summary_report(session)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
