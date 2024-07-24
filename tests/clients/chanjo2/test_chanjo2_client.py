"""Test coverage analysis API for human clinical sequencing data."""

from unittest.mock import Mock

import requests
from pytest import LogCaptureFixture
from pytest_mock import MockFixture

from cg.clients.chanjo2.client import Chanjo2APIClient
from cg.clients.chanjo2.models import CoveragePostRequest, CoveragePostResponse


def test_get_coverage_success(
    chanjo2_api_client: Chanjo2APIClient,
    coverage_post_request: CoveragePostRequest,
    coverage_post_response: CoveragePostResponse,
    coverage_post_response_success: Mock,
    mocker: MockFixture,
):
    """Tests successful get coverage extraction."""

    # GIVEN a mocked POST request
    mocker.patch.object(requests, "post", return_value=coverage_post_response_success)

    # WHEN getting the coverage data
    sample_coverage: CoveragePostResponse | None = chanjo2_api_client.get_coverage(
        coverage_post_request
    )

    # THEN the return coverage data should match the expected one
    assert sample_coverage == coverage_post_response


def test_get_coverage_exception(
    chanjo2_api_client: Chanjo2APIClient,
    coverage_post_request: CoveragePostRequest,
    coverage_post_response_exception: Mock,
    mocker: MockFixture,
    caplog: LogCaptureFixture,
):
    """Tests successful get coverage extraction."""

    # GIVEN a mocked POST request raising an exception
    mocker.patch.object(requests, "post", return_value=coverage_post_response_exception)

    # WHEN getting the coverage data
    sample_coverage: CoveragePostResponse | None = chanjo2_api_client.get_coverage(
        coverage_post_request
    )

    # THEN an exception should have been raised and the sample coverage should be None
    assert sample_coverage is None
    assert "Error during coverage POST request" in caplog.text


def test_get_coverage_empty_return(
    chanjo2_api_client: Chanjo2APIClient,
    coverage_post_request: CoveragePostRequest,
    coverage_post_response_empty: Mock,
    mocker: MockFixture,
    caplog: LogCaptureFixture,
):
    """Tests successful get coverage extraction."""

    # GIVEN a mocked POST request returning an empty JSON
    mocker.patch.object(requests, "post", return_value=coverage_post_response_empty)

    # WHEN getting the coverage data
    sample_coverage: CoveragePostResponse | None = chanjo2_api_client.get_coverage(
        coverage_post_request
    )

    # THEN an empty data error should have been thrown
    assert sample_coverage is None
    assert "The POST get coverage response is empty" in caplog.text
