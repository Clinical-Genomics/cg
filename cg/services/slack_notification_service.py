import json
import logging

import requests

LOG = logging.getLogger(__name__)


def notify(recipient: str, error: Exception):

    headers = {
        "Content-Type": "application/json",
    }
    response = requests.post(recipient, data=json.dumps({"text": str(error)}), headers=headers)
    if response.status_code != 200:
        LOG.error(f"Could not notify prod team: {response.status_code} - {response.text}")
