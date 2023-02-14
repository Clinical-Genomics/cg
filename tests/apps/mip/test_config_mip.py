import pytest

from cg.apps.mip.confighandler import ConfigHandler
from cg.exc import PedigreeConfigError


def test_validate_config(valid_config):
    """Test to validate a correct config"""
    # GIVEN a correct config

    # WHEN validating the config
    errors = ConfigHandler.validate_config(valid_config)

    # THEN assert the errors is a dict
    assert isinstance(errors, dict)

    # THEN assert there were no errors
    assert errors == {}


def test_validate_config_invalid_analysis_type(invalid_config_analysis_type):
    """Test to validate a invalid config with wrong analysis type"""
    # GIVEN invalid config, where nalaysis type is not correct

    # WHEN validating the config
    with pytest.raises(PedigreeConfigError):
        # THEN assert a config error is raised
        ConfigHandler.validate_config(invalid_config_analysis_type)


def test_validate_config_unknown_field(invalid_config_unknown_field):
    """Test to validate a config with a unspecified field.

    This should work since we allow unspecified fields
    """
    # GIVEN a correct config with a extra field

    # WHEN validating the config
    errors = ConfigHandler.validate_config(invalid_config_unknown_field)

    # THEN assert the errors is a dict
    assert isinstance(errors, dict)

    # THEN assert there where one error that could pass
    assert len(errors) == 1


def test_validate_config_unknown_field_and_missing_sample_id(
    invalid_config_unknown_field_sample_id,
):
    """Test to validate a config with a unspecified field and a missing mandatory field.
    This should raise exception since we do not allow missing mandatory fields
    """
    # GIVEN a config with missing sample_id and an extra field

    # WHEN validating the config
    with pytest.raises(PedigreeConfigError):
        # THEN assert a config error is raised
        ConfigHandler.validate_config(invalid_config_unknown_field_sample_id)


def test_validate_config_unknown_field_and_invalid_analysis_type(
    invalid_config_unknown_field_analysis_type,
):
    """Test to validate a config with a unspecified field and a invalid mandatory field.
    This should raise exception since we do not allow wrong analysis types
    """
    # GIVEN a config with wrong analysis type and an extra field

    # WHEN validating the config
    with pytest.raises(PedigreeConfigError):
        # THEN assert a config error is raised
        ConfigHandler.validate_config(invalid_config_unknown_field_analysis_type)
