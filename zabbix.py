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

    def get_event(self, eventid: str) -> dict:
        """
        Retrieves a specific event from Zabbix API.

        Returns:
            dict: Event as dict.
        """

        reqBody = {
            "jsonrpc": "2.0",
            "method": "event.get",
            "params": {
                "eventids": [eventid],
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
            return {}

        response_object = response.json()

        return response_object['result'][0]

    def get_problems(self) -> List[dict]:
        """
        Retrieves a list of active problems from Zabbix API.

        Returns:
            List[dict]: List of problems as dictionaries.
        """

        reqBody = {
            "jsonrpc": "2.0",
            "method": "problem.get",
            "params": {
                "selectTags": "extend",
                "selectAcknowledges": "extend",
                "selectSuppressionData": "extend",
                "sortfield": ["eventid"],
                "sortorder": "DESC",
            },
            "id": 1
        }

        # Do HTTP POST
        response = requests.post(url=self.api_url, data=json.dumps(reqBody), headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json-rpc"})
        if response.status_code != 200:
            response.raise_for_status()
            return []

        response_object = response.json()

        return response_object['result']