"""Test MIP config file"""

from pathlib import Path

from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile
from cg.models.mip.mip_config import MipBaseConfig


def test_instantiate_mip_config(mip_analysis_config_dna_raw: dict):
    """
    Tests mip config against a pydantic MipBaseConfig
    """
    # GIVEN a dictionary with the basic config

    # WHEN instantiating a MipBaseConfig object
    config_object = MipBaseConfig(**mip_analysis_config_dna_raw)

    # THEN assert that it was successfully created
    assert isinstance(config_object, MipBaseConfig)


def test_mip_config(mip_case_config_dna: Path):
    """Test to parse the content of a real MIP DNA config file"""
    # GIVEN the path to a file with config metadata content
    raw_config: dict = ReadFile.get_content_from_file(
        file_format=FileFormat.YAML, file_path=mip_case_config_dna
    )

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
