from unittest.mock import create_autospec

from pytest_mock import MockerFixture
from requests import Response

from cg.services import slack_notification_service
from cg.services.slack_notification_service import requests


def test_notify_success(mocker: MockerFixture):
    # GIVEN a recipient and an error
    recipient = "http://bingus.gov"
    message = "This is the problem"

    post_mock = mocker.patch.object(
        requests, "post", return_value=create_autospec(Response, status_code=200)
    )

    # WHEN calling notify
    slack_notification_service.notify(recipient=recipient, message=message)

    # THEN a http post should have been sent
    post_mock.assert_called_once_with(
        url="http://bingus.gov",
        data='{"text": "This is the problem"}',
        headers={"Content-Type": "application/json"},
    )
