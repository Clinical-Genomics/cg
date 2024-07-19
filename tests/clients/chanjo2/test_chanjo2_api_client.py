"""Test coverage analysis API for human clinical sequencing data."""

from unittest.mock import Mock

import requests
from pytest_mock import MockFixture

from cg.clients.chanjo2.api import Chanjo2APIClient
from cg.clients.chanjo2.models import CoverageData, CoverageRequest


def test_get_coverage_success(
    chanjo2_api_client: Chanjo2APIClient,
    coverage_request: CoverageRequest,
    coverage_data: CoverageData,
    successful_coverage_post_response: Mock,
    mocker: MockFixture,
):
    """Tests successful get coverage extraction."""

    # GIVEN a mocked POST request
    mocker.patch.object(requests, "post", return_value=successful_coverage_post_response)

    # WHEN getting the coverage data
    sample_coverage: CoverageData = chanjo2_api_client.get_coverage(coverage_request)

    # THEN the return coverage data should match the expected one
    assert sample_coverage == coverage_data
