"""Test some of the core functionality of the hk api"""

import pytest
from sqlalchemy.exc import OperationalError

from cg.apps.housekeeper.hk import HousekeeperAPI


def test_non_initialised_db(hk_config):
    """Test to use a database that is not initialised"""
    # GIVEN a housekeeper api and some hk configs
    HousekeeperAPI.__instance = None
    api = HousekeeperAPI.get_instance(hk_config)
    # GIVEN a api without the database
    with pytest.raises(OperationalError):
        # THEN it should raise a operational error
        api.add_tag("a-tag")


def test_init_db(hk_config):
    """Test to setup the database"""
    # GIVEN a housekeeper api and some hk configs
    HousekeeperAPI.__instance = None
    api = HousekeeperAPI.get_instance(hk_config)

    # WHEN initiating the database
    api.initialise_db()

    # THEN the api should work
    assert api.add_tag("a-tag")


def test_singleton(hk_config):
    """Test to setup the database"""
    # GIVEN a housekeeper api and some hk configs
    HousekeeperAPI.__instance = None
    hk_api_1 = HousekeeperAPI.get_instance(hk_config)

    # WHEN getting instance second time
    hk_api_2 = HousekeeperAPI.get_instance(hk_config)

    # THEN they should point to the same database session
    assert hk_api_1._store.session == hk_api_2._store.session


def test_singleton_constructor(hk_config):
    """Test to setup the database"""
    # GIVEN a housekeeper api and some hk configs
    HousekeeperAPI.__instance = None
    HousekeeperAPI(hk_config)

    # WHEN using the constructor second time
    with pytest.raises(Exception):
        # THEN it should raise an exception
        HousekeeperAPI(hk_config)
