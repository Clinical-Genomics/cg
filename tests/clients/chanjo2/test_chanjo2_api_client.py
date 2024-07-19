"""Test coverage analysis API for human clinical sequencing data."""

from unittest.mock import Mock

import requests
from pytest import LogCaptureFixture
from pytest_mock import MockFixture

from cg.clients.chanjo2.api import Chanjo2APIClient
from cg.clients.chanjo2.models import CoverageData, CoverageRequest


def test_get_coverage_success(
    chanjo2_api_client: Chanjo2APIClient,
    coverage_request: CoverageRequest,
    coverage_data: CoverageData,
    coverage_post_response_success: Mock,
    mocker: MockFixture,
):
    """Tests successful get coverage extraction."""

    # GIVEN a mocked POST request
    mocker.patch.object(requests, "post", return_value=coverage_post_response_success)

    # WHEN getting the coverage data
    sample_coverage: CoverageData | None = chanjo2_api_client.get_coverage(coverage_request)

    # THEN the return coverage data should match the expected one
    assert sample_coverage == coverage_data


def test_get_coverage_exception(
    chanjo2_api_client: Chanjo2APIClient,
    coverage_request: CoverageRequest,
    coverage_post_response_exception: Mock,
    mocker: MockFixture,
    caplog: LogCaptureFixture,
):
    """Tests successful get coverage extraction."""

    # GIVEN a mocked POST request raising an exception
    mocker.patch.object(requests, "post", return_value=coverage_post_response_exception)

    # WHEN getting the coverage data
    sample_coverage: CoverageData | None = chanjo2_api_client.get_coverage(coverage_request)

    # THEN an exception should have been raised and the sample coverage should be None
    assert sample_coverage is None
    assert "Error during coverage POST request" in caplog.text
