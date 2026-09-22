import json
import logging
import traceback
from http import HTTPStatus
from typing import Annotated, Any

import requests
from pydantic import BaseModel, BeforeValidator, Field

LOG = logging.getLogger(__name__)


def _convert_error(exception: Any) -> str | None:
    if isinstance(exception, Exception):
        return "".join(traceback.format_exception(exception))
    else:
        return exception


class SlackNotification(BaseModel):
    title: str
    message: str
    error_text: Annotated[str | None, BeforeValidator(_convert_error)] = Field(
        default=None, alias="error"
    )


def _build_slack_notification(notification: SlackNotification) -> dict:

    return {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{notification.title}*\n{notification.message}",
                },
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"```{notification.error_text}\n```"},
            },
        ],
    }


def notify(recipient: str, notification: SlackNotification):
    headers = {
        "Content-Type": "application/json",
    }
    notification_dict = _build_slack_notification(notification)
    response = requests.post(
        url=recipient,
        data=json.dumps(notification_dict),
        headers=headers,
    )
    if response.status_code != HTTPStatus.OK:
        LOG.error(f"Could not notify prod team: {response.status_code} - {response.text}")
