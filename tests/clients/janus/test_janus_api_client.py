"""Module to test Janus API client."""

from http import HTTPStatus

import pytest
import requests
from pytest_mock import MockFixture

from cg.clients.janus.api import JanusAPIClient
from cg.clients.janus.dto.create_qc_metrics_request import CreateQCMetricsRequest
from cg.clients.janus.exceptions import JanusClientError


def test_qc_metrics_successful(
    mocker: MockFixture,
    client: JanusAPIClient,
    collect_qc_request_balsamic_wgs: CreateQCMetricsRequest,
):
    # GIVEN a mocked response from the requests.post method that is successfull
    mocked_post = mocker.patch.object(requests, "post")
    mocked_response = mocker.Mock()
    mocked_response.status_code = HTTPStatus.OK
    mocked_response.json.return_value = {"data": "returned"}
    mocked_post.return_value = mocked_response

    # WHEN retrieving the qc metrics
    jobs_response: dict = client.qc_metrics(collect_qc_request_balsamic_wgs)

    # THEN the qc metrics are deserialized without error
    assert jobs_response == {"data": "returned"}

    # Additional assertions for the mocked requests.post
    mocked_post.assert_called_once_with(
        f"{client.host}/collect_qc_metrics",
        data=collect_qc_request_balsamic_wgs.model_dump_json(),
    )
    mocked_response.json.assert_called_once()


def test_qc_metrics_not_successful(
    mocker: MockFixture,
    client: JanusAPIClient,
    collect_qc_request_balsamic_wgs: CreateQCMetricsRequest,
):
    # GIVEN a mocked response from the requests.post method that is not successfull
    mocked_post = mocker.patch.object(requests, "post")
    mocked_response = mocker.Mock()
    mocked_response.status_code = HTTPStatus.NOT_FOUND
    mocked_response.json.return_value = {"data": "returned"}
    mocked_post.return_value = mocked_response

    # WHEN retrieving the qc metrics

    # THEN the request raises an error
    with pytest.raises(JanusClientError):
        client.qc_metrics(collect_qc_request_balsamic_wgs)
