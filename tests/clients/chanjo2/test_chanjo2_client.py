"""Test coverage analysis API for human clinical sequencing data."""

from unittest.mock import Mock

import pytest
import requests
from pytest_mock import MockFixture

from cg.clients.chanjo2.client import Chanjo2APIClient
from cg.clients.chanjo2.models import CoveragePostRequest, CoveragePostResponse
from cg.exc import Chanjo2RequestError, Chanjo2ResponseError


def test_post_coverage_success(
    chanjo2_api_client: Chanjo2APIClient,
    coverage_post_request: CoveragePostRequest,
    coverage_post_response: CoveragePostResponse,
    coverage_post_response_success: Mock,
    mocker: MockFixture,
):
    """Test successful POST request coverage extraction."""

    # GIVEN a mocked POST request
    mocker.patch.object(requests, "post", return_value=coverage_post_response_success)

    # WHEN getting the coverage data
    sample_coverage: CoveragePostResponse = chanjo2_api_client.get_coverage(coverage_post_request)

    # THEN the returned coverage data should match the expected one
    assert sample_coverage == coverage_post_response


def test_get_coverage_http_error(
    chanjo2_api_client: Chanjo2APIClient,
    coverage_post_request: CoveragePostRequest,
    coverage_post_response_http_error: Mock,
    mocker: MockFixture,
):
    """Test the raising of an HTTPError during POST request coverage extraction."""

    # GIVEN a mocked POST request raising an exception
    mocker.patch.object(requests, "post", return_value=coverage_post_response_http_error)

    # WHEN getting the coverage data

    # THEN a Chanjo2 request error should have been raised
    with pytest.raises(Chanjo2RequestError):
        chanjo2_api_client.get_coverage(coverage_post_request)


def test_get_coverage_validation_error(
    chanjo2_api_client: Chanjo2APIClient,
    coverage_post_request: CoveragePostRequest,
    coverage_post_response_invalid: Mock,
    mocker: MockFixture,
):
    """Test the raising of a ValidationError during POST request coverage extraction."""

    # GIVEN a mocked POST request returning an invalid JSON
    mocker.patch.object(requests, "post", return_value=coverage_post_response_invalid)

    # WHEN getting the coverage data

    # THEN a Chanjo2 response error should have been raised
    with pytest.raises(Chanjo2ResponseError):
        chanjo2_api_client.get_coverage(coverage_post_request)


# TODO: empty response
# TODO: attribute error check
