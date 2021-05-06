"""Test MIP sampleinfo file"""

from cg.apps.mip.parse_sampleinfo import MipBaseConfig, parse_config


def test_instantiate_mip_config(config_data_dna_raw: dict):
    """
    Tests parse_config against a pydantic MipBaseConfig
    """
    # GIVEN a dictionary with the basic config

    # WHEN instantiating a MipBaseConfig object
    config_object = MipBaseConfig(**config_data_dna_raw)

    # THEN assert that it was successfully created
    assert isinstance(config_object, MipBaseConfig)


def test_parse_config(config_data_dna_raw: dict, config_data_dna: dict):
    """
    Tests parse_config dict
    """
    # GIVEN a dictionary with the basic config

    # WHEN parsing raw mip config data
    mip_config = parse_config(config_data_dna_raw)

    # THEN assert that it was successfully parsed
    assert mip_config == config_data_dna
