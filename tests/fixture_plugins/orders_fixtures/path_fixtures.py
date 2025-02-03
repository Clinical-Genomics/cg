from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def cgweb_orders_dir(fixtures_dir: Path) -> Path:
    """Return the path to the cgweb_orders dir."""
    return Path(fixtures_dir, "cgweb_orders")


@pytest.fixture(scope="session")
def invalid_cgweb_orders_dir(fixtures_dir: Path) -> Path:
    """Return the path to the invalid_cgweb_orders dir."""
    return Path(fixtures_dir, "invalid_cgweb_orders")
