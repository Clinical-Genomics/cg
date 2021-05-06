"""Test MIP sampleinfo file"""

from cg.apps.mip.parse_sampleinfo import (
    MipBaseConfig,
    MipBaseSampleinfo,
    parse_config,
    parse_sampleinfo,
)


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


def test_instantiate_mip_sampleinfo(sampleinfo_data_raw: dict):
    """
    Tests parse_config against a pydantic MipBaseSampleinfo
    """
    # GIVEN a dictionary with the basic config

    # WHEN instantiating a MipBaseSampleinfo object
    sampleinfo_object = MipBaseSampleinfo(**sampleinfo_data_raw)

    # THEN assert that it was successfully created
    assert isinstance(sampleinfo_object, MipBaseSampleinfo)


def test_parse_sampleinfo(sampleinfo_data_raw: dict, sampleinfo_data: dict):
    """
    Tests parse_sampleinfo dict
    """
    # GIVEN a dictionary with the basic config

    # WHEN parsing raw mip sampleinfo data
    sampleinfo_parsed = parse_sampleinfo(sampleinfo_data_raw)

    # THEN assert that it was successfully parsed
    assert sampleinfo_parsed == sampleinfo_data
