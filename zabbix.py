import json
from typing import List, Dict

import requests


class Zabbix:
    """
    Zabbix API client

    Uses JSON-RPC 2.0 and an api token for auth
    """
    def __init__(self, api_url: str, api_key: str):
        """
        Initializes a Zabbix API client.

        Args:
            api_url (str): Complete URL of the Zabbix API.
            api_key (str): API token for authentication.
        """
        self.api_key = api_key
        self.api_url = api_url

    def get_problems(self) -> List[Dict]:
        """
        Retrieves a list of problems from Zabbix API.

        Returns:
            List[Dict]: List of problems as dictionaries.
        """

        reqBody = {
            "jsonrpc": "2.0",
            "method": "event.get",
            "params": {
                "selectTags": "extend",
                "selectHosts": ["name"],
                "sortfield": ["eventid"],
                "sortorder": "DESC",
                "filter": {
                    "value": "1"
                }
            },
            "id": 1
        }

        # Do HTTP POST
        response = requests.post(url=self.api_url, data=json.dumps(reqBody), headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json-rpc"})
        if response.status_code != 200:
            response.raise_for_status()
            return []

        response_object = response.json()

        # Filter out events with non-zero r_eventid as those are already resolved
        filtered_events = [event for event in response_object['result'] if event.get('r_eventid', 0) == '0']

        return filtered_events