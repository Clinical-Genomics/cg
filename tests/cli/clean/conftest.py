"""Fixtures for cli clean tests"""

import pytest


@pytest.fixture
def clean_context(base_store, housekeeper_api, helpers, tmpdir) -> dict:
    """context to use in cli"""

    return {
        "hk_api": housekeeper_api,
        "store_api": base_store,
        "balsamic": {"root": tmpdir,},
    }
