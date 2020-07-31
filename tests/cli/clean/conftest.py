"""Fixtures for cli clean tests"""

import pytest
from tests.cli.workflow.balsamic.conftest import *

@pytest.fixture
def clean_context(base_store, housekeeper_api, balsamic_context, helpers, tmpdir) -> dict:
    """context to use in cli"""

    return dict(
        **{"hk_api": housekeeper_api, "store_api": base_store, "balsamic": {"root": tmpdir,},},
        **balsamic_context
    )
