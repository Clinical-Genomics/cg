import json
import logging
from typing import Dict, List, Optional

import requests

LOG = logging.getLogger(__name__)


class Freshdesk:
    def __init__(self, api_key: str, domain: str):
        """Initialize the Freshdesk API"""
        self.api_key = api_key
        self.domain = domain
        self.base_url = f"https://{domain}/api/v2/"

    def _make_request(self, method: str, endpoint: str, payload: Optional[Dict] = None) -> Dict:
        """Make a request to the Freshdesk API"""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        response = requests.request(
            method,
            url,
            auth=(self.api_key, "X"),
            headers=headers,
            data=json.dumps(payload) if payload else None,
        )
        if response.status_code in {200, 201}:
            return response.json()
        else:
            raise Exception(
                f"Request failed with status code {response.status_code}: {response.text}"
            )

    def post_ticket_message(
        self, ticket_id: int, message: str, private: bool = True, verbose: bool = False
    ) -> Dict:
        """
        Post a message (note) to a ticket.
        :param ticket_id: The ID of the ticket.
        :param message: The content of the message.
        :param private: Whether the message should be private or visible to the customer.
        :param verbose: Whether to print a success message.
        :return: Details of the posted message.
        """

        html_message = (
            message.replace("\x85", "<br>")
            .replace("\u2028", "<br>")
            .replace("\u2029", "<br>")
            .replace("\r\n", "<br>")
            .replace("\r", "<br>")
            .replace("\n", "<br>")
            .replace("\\n", "<br>")
        )

        endpoint = f"/tickets/{ticket_id}/notes"
        payload = {"body": html_message, "private": private}

        print("Payload being sent:", json.dumps(payload, indent=2))

        response = self._make_request("POST", endpoint, payload)

        if "id" in response:
            if verbose:
                print(
                    f"Message successfully posted to ticket {ticket_id} (Note ID: {response['id']})."
                )
        else:
            raise Exception(
                "Message posting was successful but the response is missing expected fields."
            )

        return {"body": response.get("body")}

    def get_ticket(self, ticket_id: int, verbose: bool = False) -> Dict:
        """Retrieve ticket details by ID"""
        response = self._make_request("GET", f"/tickets/{ticket_id}")
        if verbose:
            print(f"Ticket {ticket_id} details retrieved.")
        return response

    def update_ticket(self, ticket_id: int, updates: Dict) -> Dict:
        """Update ticket details (e.g., status, priority)"""
        return self._make_request("PUT", f"/tickets/{ticket_id}", updates)

    def get_ticket_tags(self, ticket_id: int) -> List[str]:
        """
        Retrieve the tags associated with a ticket.
        :param ticket_id: The ID of the ticket.
        :return: List of tags.
        """
        ticket = self.get_ticket(ticket_id)
        return ticket.get("tags", [])

    def set_ticket_status(self, ticket_id: int, status: int) -> Dict:
        """
        Update the status of a ticket.
        :param ticket_id: The ID of the ticket.
        :param status: The new status code.
        :return: Updated ticket details.
        """
        updates = {"status": status}
        return self.update_ticket(ticket_id, updates)

    def get_ticket_group(self, ticket_id: int) -> List[str]:
        """
        Retrieve the groups associated with a ticket.
        :param ticket_id:
        :return: List of groups.
        """
        ticket = self.get_ticket(ticket_id)
        return ticket.get("group_id", [])

    def set_ticket_group(self, ticket_id: int, group_id: int) -> int:
        """
        Update the group associated with a ticket.
        :param ticket_id: ID of the ticket to update.
        :param group_id: ID of the group to assign.
        :return: The group_id assigned to the ticket.
        """
        updates = {"group_id": group_id}
        self.update_ticket(ticket_id, updates)
        return self.get_ticket(ticket_id)["group_id"]

    def add_ticket_tag(self, ticket_id: int, tag: str, verbose: bool = False) -> Dict:
        """
        Add a tag to a ticket.
        :param ticket_id: The ID of the ticket.
        :param tag: The tag to add.
        :return: Updated ticket details.
        """
        ticket = self.get_ticket(ticket_id)
        tags = ticket.get("tags", [])
        if tag not in tags:
            tags.append(tag)
        if verbose:
            print(f"Tag '{tag}' added to ticket {ticket_id}.")
        return self.update_ticket(ticket_id, {"tags": tags})

    def remove_ticket_tag(self, ticket_id: int, tag: str, verbose: bool = False) -> Dict:
        """
        Remove a tag from a ticket.
        :param ticket_id: The ID of the ticket.
        :param tag: The tag to remove.
        :return: Updated ticket details.
        """
        ticket = self.get_ticket(ticket_id)
        tags = ticket.get("tags", [])
        if tag in tags:
            tags.remove(tag)
        else:
            if verbose:
                print(f"Tag '{tag}' not found in ticket {ticket_id}. No changes made.")
            return ticket
        response = self.update_ticket(ticket_id, {"tags": tags})
        if verbose:
            print(f"Tag '{tag}' removed from ticket {ticket_id}.")
        return response

    def get_ticket_status(self, ticket_id: int, verbose: bool = False) -> str:
        """
        Retrieve the status of a ticket.
        :param ticket_id: The ID of the ticket.
        :param verbose: Whether to return a human-readable status.
        :return: Status code or status string.
        """
        ticket = self.get_ticket(ticket_id)
        status = ticket.get("status")
        if verbose:
            status_mapping = {2: "Open", 3: "Pending", 4: "Resolved", 5: "Closed"}
            return status_mapping.get(status, "Unknown")
        return status
