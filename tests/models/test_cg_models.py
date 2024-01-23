import logging

from cg.models.cg_config import CGConfig
from cg.store.store import Store


def test_instantiate_correct_configs(base_config_dict: dict):
    # GIVEN a dictionary with the basic configs

    # WHEN instantiating a CGConfig object
    config_object = CGConfig(**base_config_dict)

    # THEN assert that it was successfully created
    assert isinstance(config_object, CGConfig)


def test_fetching_the_status_db(base_config_dict: dict, caplog):
    caplog.set_level(logging.DEBUG)
    # GIVEN a dictionary with the basic configs

    # WHEN instantiating a CGConfig object
    config_object = CGConfig(**base_config_dict)

    # THEN assert that the status db exists
    assert isinstance(config_object.status_db, Store)
    # THEN assert that it was communicated that it was instantiated
    assert "Instantiating status db" in caplog.text


def test_api_instantiated_once(base_config_dict: dict, caplog):
    caplog.set_level(logging.DEBUG)
    # GIVEN a dictionary with the basic configs
    # GIVEN a CGConfig object
    config_object = CGConfig(**base_config_dict)

    # WHEN fetching (instantiating) the status_db

    # THEN assert that it was only instantiated once
    config_object.status_db
    assert "Instantiating status db" in caplog.text
    caplog.clear()
    config_object.status_db
    assert "Instantiating status db" not in caplog.text
