"""Fixtures for the shipping api tests"""

from pathlib import Path

from tests.apps.shipping.conftest import (
    fixture_shipping_configs,
    fixture_binary_path,
    fixture_host_config,
)

import pytest


@pytest.fixture(name="scout_config")
def fixture_scout_config(apps_dir: Path) -> Path:
    """Return the path to a shipping config for scout"""
    return apps_dir / "shipping" / "scout-deploy.yaml"
