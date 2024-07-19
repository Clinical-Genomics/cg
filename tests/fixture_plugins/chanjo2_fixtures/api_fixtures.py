"""Chanjo2 API fixtures."""

from typing import Any
from unittest.mock import Mock

import pytest

from cg.clients.chanjo2.api import Chanjo2APIClient


@pytest.fixture
def chanjo2_api_client(context_config: dict[str, Any]) -> Chanjo2APIClient:
    return Chanjo2APIClient(context_config)


@pytest.fixture
def json_coverage_post_response(sample_id: str) -> dict[str, float]:
    return {
        sample_id: {
            "mean_coverage": 55.55,
            "coverage_completeness_percent": 33.33,
        }
    }


@pytest.fixture
def successful_coverage_post_response(json_coverage_post_response: dict[str, float]) -> Mock:
    post_response = Mock()
    post_response.json.return_value = json_coverage_post_response
    return post_response
