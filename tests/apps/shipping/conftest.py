"""Fixtures for the shipping api tests"""

from typing import Dict
from pathlib import Path
import pytest

from cg.apps.shipping import ShippingAPI


@pytest.fixture(name="binary_path")
def fixture_binary_path() -> Path:
    return Path("path/to/shipping")


@pytest.fixture(name="host_config")
def fixture_host_config() -> Path:
    return Path("path/to/host_config.yml")


@pytest.fixture(name="shipping_configs")
def fixture_shipping_configs(binary_path: Path, host_config: Path) -> Dict[str, str]:
    return dict(host_config=str(host_config), binary_path=str(binary_path))


@pytest.fixture(name="shipping_api")
def fixture_shipping_api(shipping_configs: Dict[str, str]) -> ShippingAPI:
    api = ShippingAPI(config=shipping_configs)
    api.set_dry_run(dry_run=True)
    return api
