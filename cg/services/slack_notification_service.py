import json
import logging
from http import HTTPStatus

import requests

LOG = logging.getLogger(__name__)


def notify(recipient: str, message: str):
    headers = {
        "Content-Type": "application/json",
    }
    response = requests.post(url=recipient, data=json.dumps({"text": message}), headers=headers)
    if response.status_code != HTTPStatus.OK:
        LOG.error(f"Could not notify prod team: {response.status_code} - {response.text}")
