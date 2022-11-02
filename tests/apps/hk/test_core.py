"""Test some of the core functionality of the Housekeeper API."""

import pytest
from sqlalchemy.exc import OperationalError

from cg.apps.housekeeper.hk import HousekeeperAPI


def test_non_initialised_db(hk_config: dict, hk_tag: str):
    """Test to use a database that is not initialised."""
    # GIVEN a housekeeper api and some Housekeeper configs
    api = HousekeeperAPI(hk_config)

    # GIVEN a api without the database
    with pytest.raises(OperationalError):
        # THEN it should raise a operational error
        api.add_tag(hk_tag)


def test_init_db(hk_config: dict, hk_tag: str):
    """Test to setup the database."""
    # GIVEN a Housekeeper API and a Housekeeper config
    api = HousekeeperAPI(hk_config)

    # WHEN initiating the database
    api.initialise_db()

    # THEN the api should not throw an exception
    assert api.add_tag(hk_tag)
