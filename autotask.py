import json
import os
import random
import urllib.parse
from typing import Dict

import pytz
import requests
from datetime import datetime, timezone, tzinfo


class Autotask:
    def __init__(self, args, api_url: str, username: str, api_secret: str, api_integration_code: str):
        self.args = args
        self.api_url = api_url
        self.username = username
        self.api_secret = api_secret
        self.api_integration_code = api_integration_code

    def get_customer_company(self, name: str) -> Dict:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "ApiIntegrationCode": self.api_integration_code,
            "UserName": self.username,
            "Secret": self.api_secret,
        }

        url_with_params = f"{self.api_url}/Companies/query?search={urllib.parse.quote_plus(f'{{\"filter\":[{{\"op\":\"contains\",\"field\":\"CompanyName\",\"value\":\"{name}\"}}]}}')}"
        response = requests.get(url=url_with_params, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to get customer company: {response.text}")

        response_object = response.json()
        if response_object["pageDetails"]["count"] != 1:
            raise Exception(f"Found {response_object['pageDetails']['count']} companies with name {name}. Expected 1.")

        return response_object["items"][0]

    def create_ticket(self, problem: Dict) -> int:
        """
        Function to create an Autotask ticket.
        """
        if self.args.dry:
            ticket_id = random.randint(1, 100000)
            print(f"Created a fake Autotask ticket {ticket_id} for Zabbix event {problem['eventid']}")
            return ticket_id

        problem_start = datetime.fromtimestamp(int(problem["clock"]), tz=pytz.timezone("Europe/Helsinki"))

        customer_in_tag = ""
        for tag in problem["tags"]:
            if tag["tag"] == "customer":
                customer_in_tag = tag["value"]

        if customer_in_tag == "":
            raise Exception("Failed to find customer company. No customer tag found.")

        customer_company = self.get_customer_company(customer_in_tag)

        type_tag = ""
        for tag in problem["tags"]:
            if tag["tag"] == "type":
                type_tag = tag["value"]
                break

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "ApiIntegrationCode": self.api_integration_code,
            "UserName": self.username,
            "Secret": self.api_secret,
        }

        request_body = {
            "status": 1,
            "priority": 3, #TODO: Relative to problem severity?
            "queueID": int(os.getenv("AUTOTASK_TICKET_QUEUE_ID")),
            "companyID": customer_company["id"],
            "ticketType": int(os.getenv("AUTOTASK_TICKET_TYPE")),
            "description": f"Problem title: {problem['name']}\n"+
            f"Host name: {problem['hosts'][0]['name']}\n"+
            f"Problem started at: {problem_start.strftime('%d/%m/%Y %H:%M:%S')}\n"+
            f"Operation data(if any): {problem['opdata']}\n\n"+
            f"This ticket will be resolved automatically when the problem is resolved in Zabbix.",
            "ticketCategory": int(os.getenv("AUTOTASK_TICKET_CATEGORY")),
            "title": f"{problem['name']} {f"type:{type_tag}" if type_tag != '' else ''}"
        }

        response = requests.post(url=self.api_url+"/Tickets", data=json.dumps(request_body), headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to create ticket: {response.text}")

        ticket_id = response.json()["itemId"]

        print(f"Created Autotask ticket {ticket_id} for Zabbix event {problem['eventid']}")
        return ticket_id

    def resolve_ticket(self, ticket_id: int, resolution: str = "Resolved automatically"):
        """
        Function to resolve an Autotask ticket.
        """

        if self.args.dry:
            return

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "ApiIntegrationCode": self.api_integration_code,
            "UserName": self.username,
            "Secret": self.api_secret,
        }
        request_body = f"""{{"id": {ticket_id}, "status": 5, "resolution": "{resolution}"}}"""

        response = requests.patch(url=self.api_url+"/Tickets", data=request_body, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to resolve ticket {ticket_id}: {response.text}")
