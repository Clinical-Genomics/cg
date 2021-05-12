"""Test MIP config file"""

from pathlib import Path

import yaml

from cg.models.mip.mip_config import MipBaseConfig, parse_config


def test_instantiate_mip_config(mip_analysis_config_dna_raw: dict):
    """
    Tests parse_config against a pydantic MipBaseConfig
    """
    # GIVEN a dictionary with the basic config

    # WHEN instantiating a MipBaseConfig object
    config_object = MipBaseConfig(**mip_analysis_config_dna_raw)

    # THEN assert that it was successfully created
    assert isinstance(config_object, MipBaseConfig)


def test_parse_config(mip_analysis_config_dna_raw: dict, mip_analysis_config_dna: MipBaseConfig):
    """
    Tests parse_config dict
    """
    # GIVEN a dictionary with the basic config

    # WHEN parsing raw mip config data
    mip_config = parse_config(mip_analysis_config_dna_raw)

    # THEN assert that it was successfully parsed
    assert mip_config == mip_analysis_config_dna


def test_mip_config(mip_case_config_dna: Path):
    """Test to parse the content of a real MIP DNA config file"""
    # GIVEN the path to a file with config metadata content
    with open(mip_case_config_dna, "r") as config_handle:
        raw_config = yaml.full_load(config_handle)

    # WHEN instantiating a MipBaseSampleInfo object
    config_object = MipBaseConfig(**raw_config)

    # THEN assert that it was successfully created
    assert isinstance(config_object, MipBaseConfig)


def test_mip_config_case_id(mip_analysis_config_dna_raw: dict):
    """Test case_id validator"""
    # GIVEN a MIP config

    # WHEN instantiating a MipBaseSampleInfo object
    config_object = MipBaseConfig(**mip_analysis_config_dna_raw)

    # THEN assert that case_id was set
    assert config_object.case_id == "yellowhog"


def test_mip_config_case_id_with_family_id(mip_analysis_config_dna_raw: dict):
    """Test case_id validator"""
    # GIVEN a MIP config missing a case_id but with family_id
    mip_analysis_config_dna_raw.pop("case_id")

    # WHEN instantiating a MipBaseSampleInfo object
    config_object = MipBaseConfig(**mip_analysis_config_dna_raw)

    # THEN assert that case_id was set
    assert config_object.case_id == "a_family_id"


def test_mip_config_case_id(mip_analysis_config_dna_raw: dict):
    """Test case_id validator"""
    # GIVEN a MIP config

    # WHEN instantiating a MipBaseSampleInfo object
    config_object = MipBaseConfig(**mip_analysis_config_dna_raw)

    # THEN assert that samples was set
    assert config_object.samples

    # THEN assert that dict is set
    analysis_type: dict = config_object.samples.pop()
    assert analysis_type == {"analysis_type": "wgs", "sample_id": "sample_id"}
