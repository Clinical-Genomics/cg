"""Chanjo2 API fixtures."""

from typing import Any
from unittest.mock import Mock

import pytest
import requests

from cg.clients.chanjo2.client import Chanjo2APIClient


@pytest.fixture
def chanjo2_api_client(context_config: dict[str, Any]) -> Chanjo2APIClient:
    return Chanjo2APIClient(context_config)


@pytest.fixture
def coverage_post_response_json(sample_id: str) -> dict[str, float]:
    return {
        sample_id: {
            "mean_coverage": 55.55,
            "coverage_completeness_percent": 33.33,
        }
    }


@pytest.fixture
def coverage_post_response_success(coverage_post_response_json: dict[str, float]) -> Mock:
    post_response = Mock()
    post_response.json.return_value = coverage_post_response_json
    return post_response


@pytest.fixture
def coverage_post_response_exception() -> Mock:
    post_response = Mock()
    post_response.raise_for_status.side_effect = requests.HTTPError("An error occurred")
    return post_response


@pytest.fixture
def coverage_post_response_empty() -> Mock:
    post_response = Mock()
    post_response.json.return_value = {}
    return post_response
