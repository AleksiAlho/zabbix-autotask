import argparse
import os
import time
import sqlite3
import logging

import dotenv

from zabbix import Zabbix
from autotask import Autotask

dotenv.load_dotenv(".env")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Params
parser = argparse.ArgumentParser()
parser.add_argument("--dry", "-dry", action="store_true", help="Dry run to skip autotask API calls and use mock IDs instead")
parser.add_argument("--once", "-once", action="store_true", help="Run sync once and exit")
args = parser.parse_args()

DB_PATH = os.getenv("DB_PATH")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS problems (
            eventid TEXT PRIMARY KEY,
            ticket_id TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_stored_problems():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT eventid, ticket_id FROM problems')
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

def store_problem(eventid, ticket_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO problems (eventid, ticket_id) VALUES (?, ?)', (eventid, ticket_id))
    conn.commit()
    conn.close()

def delete_problem(eventid):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM problems WHERE eventid = ?', (eventid,))
    conn.commit()
    conn.close()

def run_sync():
    zabbix = Zabbix(api_url=os.getenv("ZABBIX_API_URL"),
                    api_key=os.getenv("ZABBIX_API_KEY"))
    autotask = Autotask(args=args,
                        api_url=os.getenv("AUTOTASK_API_URL"),
                        username=os.getenv("AUTOTASK_API_USERNAME"),
                        api_secret=os.getenv("AUTOTASK_API_SECRET"),
                        api_integration_code=os.getenv("AUTOTASK_API_INTEGRATION_CODE"))

    # 0. Fetch problems from zabbix and db
    zabbix_problems = zabbix.get_problems()
    # Filter problems: only include those with tag 'trigger_autotask' == 'yes'
    zabbix_problems = [
        p for p in zabbix_problems
        if any(tag.get('tag') == 'trigger_autotask' and tag.get('value') == 'yes' for tag in p.get('tags', []))
    ]
    zabbix_eventids = {str(p['eventid']) for p in zabbix_problems}
    
    stored_problems = get_stored_problems()
    stored_eventids = set(stored_problems.keys())
    
    # 1. See if local sqlite database has any problems that don't exist in zabbix anymore
    to_delete = stored_eventids - zabbix_eventids
    for eventid in to_delete:
        ticket_id = stored_problems[eventid]
        logger.info(f"Problem {eventid} no longer in Zabbix. Resolving ticket {ticket_id}...")
        try:
            autotask.resolve_ticket(ticket_id)
            delete_problem(eventid)
        except Exception as e:
            logger.error(f"Failed to resolve ticket {ticket_id}: {e}")

    # 2. Add new problems to local sqlite database, and create a new autotask ticket
    to_add = zabbix_eventids - stored_eventids
    for eventid in to_add:
        # Get problem object from zabbix_problems with eventid
        problem = next((p for p in zabbix_problems if str(p['eventid']) == eventid), None)
        if problem is None:
            continue

        logger.info(f"New problem detected in Zabbix: {eventid}. Creating ticket...")
        ticket_id = autotask.create_ticket(problem)
        store_problem(eventid, ticket_id)

def main():
    init_db()

    if args.dry:
        logger.info(f"Dry run, autotask calls will be faked...")

    if args.once:
        logger.info("Running sync once...")
        run_sync()
        exit(0)

    logger.info("Starting sync loop, if you see no errors, we're good...")
    while True:
        try:
            run_sync()
        except Exception as e:
            logger.error(f"An error occurred: {e}. Retrying in 15 seconds...")
        
        time.sleep(15)

if __name__ == "__main__":
    main()
