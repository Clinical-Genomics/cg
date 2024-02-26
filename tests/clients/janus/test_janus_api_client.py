"""Module to test Janus API client."""

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
    janus_response: dict,
    mock_post_request_ok: MockFixture,
):
    # GIVEN a mocked response from the requests.post method that is successful
    mocked_post = mocker.patch.object(requests, "post")
    mocked_post.return_value = mock_post_request_ok

    # WHEN retrieving the qc metrics
    jobs_response: dict = client.qc_metrics(collect_qc_request_balsamic_wgs)

    # THEN the qc metrics are deserialized without error
    assert jobs_response == janus_response

    # Additional assertions for the mocked requests.post
    mocked_post.assert_called_once_with(
        f"{client.host}/collect_qc_metrics",
        data=collect_qc_request_balsamic_wgs.model_dump_json(),
    )
    mock_post_request_ok.json.assert_called_once()


def test_qc_metrics_not_successful(
    mocker: MockFixture,
    client: JanusAPIClient,
    collect_qc_request_balsamic_wgs: CreateQCMetricsRequest,
    janus_response: dict,
    mock_post_request_not_found: MockFixture,
):
    # GIVEN a mocked response from the requests.post method that is not successful
    mocked_post = mocker.patch.object(requests, "post")
    mocked_post.return_value = mock_post_request_not_found

    # WHEN retrieving the qc metrics

    # THEN the request raises an error
    with pytest.raises(JanusClientError):
        client.qc_metrics(collect_qc_request_balsamic_wgs)
