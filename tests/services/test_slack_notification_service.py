from unittest.mock import create_autospec

from pytest_mock import MockerFixture
from requests import Response

from cg.services import slack_notification_service
from cg.services.slack_notification_service import SlackNotification, requests


def test_notify_success(mocker: MockerFixture):
    # GIVEN a Slack notification and a recipient
    notification = SlackNotification(
        title="Some title", message="A message", error=Exception("An Error")  # type: ignore
    )
    recipient = "http://bingus.gov"

    post_mock = mocker.patch.object(
        requests, "post", return_value=create_autospec(Response, status_code=200)
    )

    # WHEN calling notify
    slack_notification_service.notify(recipient=recipient, notification=notification)

    # THEN a http post should have been sent
    post_mock.assert_called_once_with(
        url="http://bingus.gov",
        data='{"blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": "*Some title*\\nA message"}}, {"type": "section", "text": {"type": "mrkdwn", "text": "```Exception: An Error\\n\\n```"}}]}',
        headers={"Content-Type": "application/json"},
    )
