"""Chanjo2 API fixtures."""

from typing import Any
from unittest.mock import Mock

import pytest
import requests

from cg.clients.chanjo2.client import Chanjo2APIClient
from cg.clients.chanjo2.models import CoverageMetrics


@pytest.fixture
def chanjo2_api_client(context_config: dict[str, Any]) -> Chanjo2APIClient:
    return Chanjo2APIClient(context_config["chanjo2"]["host"])


@pytest.fixture
def coverage_post_response_json(sample_id: str) -> dict[str, dict]:
    return {
        sample_id: {
            "mean_coverage": 55.55,
            "coverage_completeness_percent": 33.33,
        }
    }


@pytest.fixture
def coverage_post_response_invalid_values_json(sample_id: str) -> dict[str, dict]:
    return {
        sample_id: {
            "mean_coverage": "I am a string",
            "coverage_completeness_percent": 33.33,
        }
    }


@pytest.fixture
def coverage_post_response_invalid_attributes_json(sample_id: str) -> dict[str, dict]:
    return {
        sample_id: {
            "not_a_metric": 55.55,
            "coverage_completeness_percent": 33.33,
        },
    }


@pytest.fixture
def coverage_post_response_success(coverage_post_response_json: dict) -> Mock:
    post_response = Mock()
    post_response.json.return_value = coverage_post_response_json
    return post_response


@pytest.fixture
def coverage_post_response_http_error() -> Mock:
    post_response = Mock()
    post_response.raise_for_status.side_effect = requests.HTTPError()
    return post_response


@pytest.fixture
def coverage_post_response_invalid_values(coverage_post_response_invalid_values_json: dict) -> Mock:
    post_response = Mock()
    post_response.json.return_value = coverage_post_response_invalid_values_json
    return post_response


@pytest.fixture
def coverage_post_response_invalid_attributes(
    coverage_post_response_invalid_attributes_json: dict,
) -> Mock:
    post_response = Mock()
    post_response.json.return_value = coverage_post_response_invalid_attributes_json
    return post_response


@pytest.fixture
def coverage_post_response_empty() -> Mock:
    post_response = Mock()
    post_response.json.return_value = {}
    return post_response


@pytest.fixture
def coverage_metrics(
    sample_id: str, coverage_post_response_json: dict[str, dict]
) -> CoverageMetrics:
    return CoverageMetrics.model_validate(coverage_post_response_json[sample_id])
