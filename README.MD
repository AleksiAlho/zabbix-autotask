# Zabbix-Autotask Integration

This tool provides automated synchronization between Zabbix problems and Autotask tickets. It monitors Zabbix for active problems and automatically creates corresponding tickets in Autotask. Once a problem is resolved in Zabbix, the tool ensures the associated Autotask ticket is also closed.

## Features

- **Automated Ticket Creation**: Creates Autotask tickets for new Zabbix problems.
- **Automated Resolution**: Closes Autotask tickets when the Zabbix problem is cleared.
- **Customer Mapping**: Maps Zabbix problems to Autotask companies using Zabbix tags (expects a `customer` tag).
- **Persistent Tracking**: Uses a local SQLite database to maintain the link between Zabbix events and Autotask tickets.
- **Continuous Sync or one-off**: Either run a loop to keep both systems in sync or a one-off sync, e.g trigger as a Zabbix media type.

## Prerequisites

- Python 3.x
- Couple of python packages
- Zabbix API access (URL and API Token)
- Autotask API access (URL, Username, Secret, and Integration Code)

## Configuration

The application is configured using environment variables. You can use a `.env` file or set them in your environment:

| Variable | Description                                                                    |
|----------|--------------------------------------------------------------------------------|
| `DB_PATH` | Path to the SQLite database (e.g., `problems.sqlite`)                          |
| `ZABBIX_API_URL` | Full URL to the Zabbix API (e.g., `https://zabbix.example.com/api_jsonrpc.php`) |
| `ZABBIX_API_KEY` | Zabbix API Token                                                               |
| `AUTOTASK_API_URL` | Autotask API Base URL (e.g., `https://webservicesX.autotask.net/atservicesrest/v1.0`) |
| `AUTOTASK_API_USERNAME` | Autotask API Username                                                          |
| `AUTOTASK_API_SECRET` | Autotask API Secret                                                            |
| `AUTOTASK_API_INTEGRATION_CODE` | Autotask API Integration Code                                                  |
| `AUTOTASK_TICKET_QUEUE_ID` | The Queue ID where tickets should be created                                   |
| `AUTOTASK_TICKET_CATEGORY` | The Category ID for new tickets                                                |
| `AUTOTASK_TICKET_TYPE` | The Ticket type ID for new tickets                                             |
| `TIMEZONE` | Target timezone for conversions                                                |

## Installation

1. Clone the repository.
2. Set up virtual env:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up your environment variables (see [Configuration](#configuration)).

## Usage

Run the main script to start the synchronization loop:

```bash
python main.py
```
The script will initialize the local database if it doesn't exist and start checking for updates every 15 seconds.

Available launch parameters:

| Parameter            | Description                      |
|----------------------|----------------------------------|
| `--once`<br/>`-once` | Run only once instead of a loop  |
| `--dry`<br/>`-dry`   | Run with fake Autotask API calls |

## How it Works
0. **Zabbix Setup**: Tag templates, hosts and/or triggers with `trigger_autotask=yes`, and `customer=Autotask customer name here`
1. **Detection**: The script fetches active problems from Zabbix.
3. **Creation**: For any new problem that isn't in the local database, it looks for a `customer` tag in Zabbix, finds the matching company in Autotask, and creates a ticket. If no matching company is found, the alert is ignored.
3. **Tracking**: The mapping between the Zabbix `eventid` and Autotask `ticket_id` is stored in `DB_PATH`.
4. **Resolution**: If a problem tracked in the database is no longer active in Zabbix, the script resolves the Autotask ticket and removes the entry from the database.
