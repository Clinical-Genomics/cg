from unittest.mock import create_autospec

from pytest_mock import MockerFixture
from requests import Response

from cg.services import slack_notification_service
from cg.services.slack_notification_service import SlackNotification, requests


def test_notify_success_with_error(mocker: MockerFixture):
    # GIVEN a Slack notification and a recipient and an error
    notification = SlackNotification(
        title="Some title", message="A message", error=Exception("An Error")  # type: ignore
    )
    recipient = "http://prod.team"

    post_mock = mocker.patch.object(
        requests, "post", return_value=create_autospec(Response, status_code=200)
    )

    # WHEN calling notify
    slack_notification_service.notify(recipient=recipient, notification=notification)

    # THEN a http post should have been sent
    post_mock.assert_called_once_with(
        url="http://prod.team",
        data='{"blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": "*Some title*\\nA message"}}, {"type": "section", "text": {"type": "mrkdwn", "text": "```Exception: An Error\\n\\n```"}}]}',
        headers={"Content-Type": "application/json"},
    )


def test_notify_success_no_error(mocker: MockerFixture):
    # GIVEN a Slack notification and a recipient and no error
    notification = SlackNotification(title="Some title", message="A message")
    recipient = "http://prod.team"

    post_mock = mocker.patch.object(
        requests, "post", return_value=create_autospec(Response, status_code=200)
    )

    # WHEN calling notify
    slack_notification_service.notify(recipient=recipient, notification=notification)

    # THEN a http post should have been sent
    post_mock.assert_called_once_with(
        url="http://prod.team",
        data='{"blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": "*Some title*\\nA message"}}]}',
        headers={"Content-Type": "application/json"},
    )
