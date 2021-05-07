"""Test MIP sample info file"""

from pathlib import Path

import yaml

from cg.apps.mip.parse_sampleinfo import parse_sampleinfo
from cg.models.mip.mip_sample_info import MipBaseSampleinfo


def test_instantiate_mip_sampleinfo(sample_info_dna_raw: dict):
    """Tests sample info against a pydantic MipBaseSampleinfo"""
    # GIVEN a dictionary with the basic config

    # WHEN instantiating a MipBaseSampleinfo object
    sample_info_object = MipBaseSampleinfo(**sample_info_dna_raw)

    # THEN assert that it was successfully created
    assert isinstance(sample_info_object, MipBaseSampleinfo)


def test_parse_sampleinfo(sample_info_dna_raw: dict, sample_info_dna: MipBaseSampleinfo):
    """Tests parse_sampleinfo dict"""
    # GIVEN a dictionary with the basic config

    # WHEN parsing raw mip sampleinfo data
    sample_info_parsed = parse_sampleinfo(sample_info_dna_raw)

    # THEN assert that it was successfully parsed
    assert sample_info_parsed == sample_info_dna


def test_mip_sampleinfo(case_qc_sample_info_path: Path):
    """Test to parse the content of a real qc_sample_info file"""
    # GIVEN the path to a file with sample_info metadata content
    with open(case_qc_sample_info_path, "r") as sample_info_handle:
        raw_sample_info = yaml.full_load(sample_info_handle)

    # WHEN instantiating a MipBaseSampleinfo object
    sample_info_object = MipBaseSampleinfo(**raw_sample_info)

    # THEN assert that it was successfully created
    assert isinstance(sample_info_object, MipBaseSampleinfo)


def test_mip_sampleinfo_case_id(sample_info_dna_raw: dict):
    """Test case_id validator"""
    # GIVEN a dictionary with the sample info data

    # WHEN instantiating a MipBaseSampleinfo object
    sample_info_object = MipBaseSampleinfo(**sample_info_dna_raw)

    # THEN assert that case_id was set
    assert sample_info_object.case_id == "yellowhog"


def test_mip_sampleinfo_case_id_with_family_id(sample_info_dna_raw: dict):
    """Test case_id validator"""
    # GIVEN a MIP sample info file missing a case_id but with family_id
    sample_info_dna_raw.pop("case_id")

    # WHEN instantiating a MipBaseSampleinfo object
    sample_info_object = MipBaseSampleinfo(**sample_info_dna_raw)

    # THEN assert that case_id was set
    assert sample_info_object.case_id == "a_family_id"


def test_mip_sampleinfo_genome_build(sample_info_dna_raw: dict):
    """Test genome_build validator"""
    # GIVEN a dictionary with the sample info data

    # WHEN instantiating a MipBaseSampleinfo object
    sample_info_object = MipBaseSampleinfo(**sample_info_dna_raw)

    # THEN assert that genome build was set
    assert sample_info_object.genome_build == "grch37"


def test_mip_sampleinfo_is_finished(sample_info_dna_raw: dict):
    """Test is_finished validator"""
    # GIVEN a dictionary with the sample info data

    # WHEN instantiating a MipBaseSampleinfo object
    sample_info_object = MipBaseSampleinfo(**sample_info_dna_raw)

    # THEN assert that is_finished was set
    assert sample_info_object.is_finished


def test_mip_sampleinfo_is_finished(sample_info_dna_raw: dict):
    """Test is_finished validator"""
    # GIVEN a dictionary with the sample info data when analysisrunstatus is not finished
    sample_info_dna_raw["analysisrunstatus"] = "not_finished"

    # WHEN instantiating a MipBaseSampleinfo object
    sample_info_object = MipBaseSampleinfo(**sample_info_dna_raw)

    # THEN assert that is_finished was set
    assert not sample_info_object.is_finished


def test_mip_sampleinfo_rank_model_version(sample_info_dna_raw: dict):
    """Test rank_model_version validator"""
    # GIVEN a dictionary with the sample info data

    # WHEN instantiating a MipBaseSampleinfo object
    sample_info_object = MipBaseSampleinfo(**sample_info_dna_raw)

    # THEN assert that rank_model_version was set
    assert not sample_info_object.rank_model_version == "v1.0"


def test_mip_sampleinfo_sv_rank_model_version(sample_info_dna_raw: dict):
    """Test sv_rank_model_version validator"""
    # GIVEN a dictionary with the sample info data

    # WHEN instantiating a MipBaseSampleinfo object
    sample_info_object = MipBaseSampleinfo(**sample_info_dna_raw)

    # THEN assert that rank_model_version was set
    assert not sample_info_object.sv_rank_model_version == "v1.2.0"
