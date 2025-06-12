"""Test coverage analysis API for human clinical sequencing data."""

from unittest.mock import Mock

import pytest
import requests
from pytest_mock import MockFixture

from cg.clients.chanjo2.client import Chanjo2APIClient
from cg.clients.chanjo2.models import (
    CoverageMetrics,
    CoveragePostRequest,
    CoveragePostResponse,
)
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
    """Test the handling of an HTTP error when getting coverage."""

    # GIVEN a mocked POST request raising an exception
    mocker.patch.object(requests, "post", return_value=coverage_post_response_http_error)

    # WHEN getting the coverage data

    # THEN a Chanjo2 request error should have been raised
    with pytest.raises(Chanjo2RequestError):
        chanjo2_api_client.get_coverage(coverage_post_request)


def test_get_coverage_invalid_values(
    chanjo2_api_client: Chanjo2APIClient,
    coverage_post_request: CoveragePostRequest,
    coverage_post_response_invalid_values: Mock,
    mocker: MockFixture,
):
    """Test handling of a validation error when getting coverage."""

    # GIVEN a mocked POST request returning a JSON with invalid values
    mocker.patch.object(requests, "post", return_value=coverage_post_response_invalid_values)

    # WHEN getting the coverage data

    # THEN a Chanjo2 response error should have been raised
    with pytest.raises(Chanjo2ResponseError):
        chanjo2_api_client.get_coverage(coverage_post_request)


def test_get_coverage_invalid_attributes(
    chanjo2_api_client: Chanjo2APIClient,
    coverage_post_request: CoveragePostRequest,
    coverage_post_response_invalid_attributes: Mock,
    mocker: MockFixture,
):
    """Test coverage POST request returning an invalid response with incorrect attributes."""

    # GIVEN a mocked POST request returning a JSON with incorrect attributes
    mocker.patch.object(requests, "post", return_value=coverage_post_response_invalid_attributes)

    # WHEN getting the coverage data

    # THEN a Chanjo2 response error should have been raised
    with pytest.raises(Chanjo2ResponseError):
        chanjo2_api_client.get_coverage(coverage_post_request)


def test_get_coverage_empty_response(
    chanjo2_api_client: Chanjo2APIClient,
    coverage_post_request: CoveragePostRequest,
    coverage_post_response_empty: Mock,
    mocker: MockFixture,
):
    """Test coverage POST request returning an empty response."""

    # GIVEN a mocked POST request returning an empty JSON
    mocker.patch.object(requests, "post", return_value=coverage_post_response_empty)

    # WHEN getting the coverage data

    # THEN a Chanjo2 response error should have been raised
    with pytest.raises(Chanjo2ResponseError):
        chanjo2_api_client.get_coverage(coverage_post_request)


def test_get_sample_coverage_metrics(
    sample_id: str,
    coverage_post_response: CoveragePostResponse,
    coverage_post_response_json: dict[str, dict],
):
    """Test sample coverage extraction from a coverage POST response."""

    # GIVEN a mocked POST response

    # WHEN getting the coverage data for a specific sample ID
    coverage_metrics: CoverageMetrics = coverage_post_response.get_sample_coverage_metrics(
        sample_id
    )

    # THEN the returned coverage metrics should match the expected one
    assert coverage_metrics.model_dump() == coverage_post_response_json[sample_id]


def test_get_sample_coverage_metrics_invalid_sample_id(
    invalid_sample_id: str, coverage_post_response: CoveragePostResponse
):
    """Test sample coverage extraction from a coverage POST response providing an invalid sample."""

    # GIVEN a mocked POST response

    # WHEN getting the coverage data for a specific sample ID

    # THEN a validation error should be raised
    with pytest.raises(ValueError):
        coverage_post_response.get_sample_coverage_metrics(invalid_sample_id)
