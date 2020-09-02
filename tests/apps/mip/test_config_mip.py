import pytest
from cg.exc import ConfigError
from cg.apps.mip.confighandler import ConfigHandler


def test_validate_config():
    """Test to validate a correct config"""
    # GIVEN a correct config
    sample = dict(
        sample_id="sample",
        analysis_type="wes",
        father="0",
        mother="0",
        phenotype="affected",
        sex="male",
        expected_coverage=15,
        capture_kit="agilent_sureselect_cre.v1",
    )

    config = dict(
        case="a_case",
        default_gene_panels=["a_panel"],
        samples=[sample],
    )

    # WHEN validating the config
    errors = ConfigHandler.validate_config(config)

    # THEN assert the errors is a dict
    assert isinstance(errors, dict)

    # THEN assert there where no errors
    assert errors == {}


def test_validate_config_invalid_analysis_type():
    """Test to validate a invalid config with wrong analysis type"""
    # GIVEN a correct config
    sample = dict(
        sample_id="sample",
        analysis_type="nonexisting",
        father="0",
        mother="0",
        phenotype="affected",
        sex="male",
        expected_coverage=15,
        capture_kit="agilent_sureselect_cre.v1",
    )

    config = dict(
        case="a_case",
        default_gene_panels=["a_panel"],
        samples=[sample],
    )

    # WHEN validating the config
    with pytest.raises(ConfigError):
        # THEN assert a config error is raised
        ConfigHandler.validate_config(config)


def test_validate_config_unknown_field():
    """Test to validate a config with a unspecified field.

    This should work since we allow unspecified fields
    """
    # GIVEN a correct config with a extra field
    sample = dict(
        sample_id="sample",
        sample_display_name="ASAMPLENAME",
        analysis_type="wes",
        father="0",
        mother="0",
        phenotype="affected",
        sex="male",
        expected_coverage=15,
        capture_kit="agilent_sureselect_cre.v1",
    )

    config = dict(
        case="a_case",
        default_gene_panels=["a_panel"],
        samples=[sample],
    )

    # WHEN validating the config
    errors = ConfigHandler.validate_config(config)

    # THEN assert the errors is a dict
    assert isinstance(errors, dict)

    # THEN assert there where one error that could pass
    assert len(errors) == 1


def test_validate_config_unknown_field_and_missing_sample_id():
    """Test to validate a config with a unspecified field and a missing mandatory field.

    This should raise exception since we do not allow missing mandatory fields
    """
    # GIVEN a config with missing sample_id and an extra field
    sample = dict(
        sample_display_name="a_sample_name",
        analysis_type="wes",
        father="0",
        mother="0",
        phenotype="affected",
        sex="male",
        expected_coverage=15,
        capture_kit="agilent_sureselect_cre.v1",
    )

    config = dict(
        case="a_case",
        default_gene_panels=["a_panel"],
        samples=[sample],
    )

    # WHEN validating the config
    with pytest.raises(ConfigError):
        # THEN assert a config error is raised
        ConfigHandler.validate_config(config)


def test_validate_config_unknown_field_and_invalid_analysis_type():
    """Test to validate a config with a unspecified field and a invalid mandatory field.

    This should raise exception since we do not allow wrong analysis types
    """
    # GIVEN a config with wrong analysis type and an extra field
    sample = dict(
        sample_id="sample",
        sample_display_name="a_sample_name,
        analysis_type="nonexisting",
        father="0",
        mother="0",
        phenotype="affected",
        sex="male",
        expected_coverage=15,
        capture_kit="agilent_sureselect_cre.v1",
    )

    config = dict(
        case="a_case",
        default_gene_panels=["a_panel"],
        samples=[sample],
    )

    # WHEN validating the config
    with pytest.raises(ConfigError):
        # THEN assert a config error is raised
        ConfigHandler.validate_config(config)
