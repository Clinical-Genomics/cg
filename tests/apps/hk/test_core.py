"""Test some of the core functionality of the hk api"""

import pytest
from sqlalchemy.exc import OperationalError

from cg.apps.housekeeper.hk import HousekeeperAPI


def test_non_initialised_db(hk_config):
    """Test to use a database that is not initialised"""
    # GIVEN a housekeeper api and some hk configs
    api = HousekeeperAPI(hk_config)
    # GIVEN a api without the database
    with pytest.raises(OperationalError):
        # THEN it should raise a operational error
        api.add_tag("a-tag")


def test_init_db(hk_config):
    """Test to setup the database"""
    # GIVEN a housekeeper api and some hk configs
    api = HousekeeperAPI(hk_config)

    # WHEN initiating the database
    api.initialise_db()

    # THEN the api should work
    assert api.add_tag("a-tag")
