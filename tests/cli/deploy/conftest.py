"""Fixtures for the shipping api tests"""

from pathlib import Path

import pytest
from cg.apps.shipping import ShippingAPI
from cg.models.cg_config import CGConfig
from tests.apps.shipping.conftest import (
    fixture_binary_path,
    fixture_host_config,
    fixture_shipping_api,
    fixture_shipping_configs,
)


@pytest.fixture(name="scout_config")
def fixture_scout_config(apps_dir: Path) -> Path:
    """Return the path to a shipping config for scout"""
    return apps_dir / "shipping" / "scout-deploy.yaml"


@pytest.fixture(name="shipping_context")
def fixture_shipping_context(base_context: CGConfig, shipping_api: ShippingAPI) -> CGConfig:
    base_context.shipping_api_ = shipping_api
    return base_context
