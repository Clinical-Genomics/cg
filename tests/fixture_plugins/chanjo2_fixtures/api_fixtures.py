"""Chanjo2 API fixtures."""

from typing import Any

import pytest

from cg.clients.chanjo2.api import Chanjo2APIClient


@pytest.fixture
def chanjo2_api_client(context_config: dict[str, Any]) -> Chanjo2APIClient:
    return Chanjo2APIClient(context_config)
