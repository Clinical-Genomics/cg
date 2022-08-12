"""Test MIP sample info file"""

from pathlib import Path

from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile
from cg.models.mip.mip_sample_info import MipBaseSampleInfo


def test_instantiate_mip_sampleinfo(sample_info_dna_raw: dict):
    """Tests sample info against a pydantic MipBaseSampleInfo"""
    # GIVEN a dictionary with the basic config

    # WHEN instantiating a MipBaseSampleInfo object
    sample_info_object = MipBaseSampleInfo(**sample_info_dna_raw)

    # THEN assert that it was successfully created
    assert isinstance(sample_info_object, MipBaseSampleInfo)


def test_mip_sampleinfo(case_qc_sample_info_path: Path):
    """Test to parse the content of a real qc_sample_info file"""
    # GIVEN the path to a file with sample_info metadata content
    raw_sample_info = ReadFile.get_content_from_file(
        file_format=FileFormat.YAML, file_path=case_qc_sample_info_path
    )

    # WHEN instantiating a MipBaseSampleInfo object
    sample_info_object = MipBaseSampleInfo(**raw_sample_info)

    # THEN assert that it was successfully created
    assert isinstance(sample_info_object, MipBaseSampleInfo)


def test_mip_sampleinfo_case_id(sample_info_dna_raw: dict):
    """Test case_id validator"""
    # GIVEN a dictionary with the sample info data

    # WHEN instantiating a MipBaseSampleInfo object
    sample_info_object = MipBaseSampleInfo(**sample_info_dna_raw)

    # THEN assert that case_id was set
    assert sample_info_object.case_id == "yellowhog"


def test_mip_sampleinfo_case_id_with_family_id(sample_info_dna_raw: dict):
    """Test case_id validator"""
    # GIVEN a MIP sample info file missing a case_id but with family_id
    sample_info_dna_raw.pop("case_id")

    # WHEN instantiating a MipBaseSampleInfo object
    sample_info_object = MipBaseSampleInfo(**sample_info_dna_raw)

    # THEN assert that case_id was set
    assert sample_info_object.case_id == "a_family_id"


def test_mip_sampleinfo_genome_build(sample_info_dna_raw: dict):
    """Test genome_build validator"""
    # GIVEN a dictionary with the sample info data

    # WHEN instantiating a MipBaseSampleInfo object
    sample_info_object = MipBaseSampleInfo(**sample_info_dna_raw)

    # THEN assert that genome build was set
    assert sample_info_object.genome_build == "grch37"


def test_mip_sampleinfo_is_finished(sample_info_dna_raw: dict):
    """Test is_finished validator"""
    # GIVEN a dictionary with the sample info data

    # WHEN instantiating a MipBaseSampleInfo object
    sample_info_object = MipBaseSampleInfo(**sample_info_dna_raw)

    # THEN assert that is_finished was set
    assert sample_info_object.is_finished


def test_mip_sampleinfo_is_finished(sample_info_dna_raw: dict):
    """Test is_finished validator"""
    # GIVEN a dictionary with the sample info data when analysisrunstatus is not finished
    sample_info_dna_raw["analysisrunstatus"] = "not_finished"

    # WHEN instantiating a MipBaseSampleInfo object
    sample_info_object = MipBaseSampleInfo(**sample_info_dna_raw)

    # THEN assert that is_finished was set
    assert not sample_info_object.is_finished


def test_mip_sampleinfo_rank_model_version(sample_info_dna_raw: dict):
    """Test rank_model_version validator"""
    # GIVEN a dictionary with the sample info data

    # WHEN instantiating a MipBaseSampleInfo object
    sample_info_object = MipBaseSampleInfo(**sample_info_dna_raw)

    # THEN assert that rank_model_version was set
    assert sample_info_object.rank_model_version == "v1.0"


def test_mip_sampleinfo_sv_rank_model_version(sample_info_dna_raw: dict):
    """Test sv_rank_model_version validator"""
    # GIVEN a dictionary with the sample info data

    # WHEN instantiating a MipBaseSampleInfo object
    sample_info_object = MipBaseSampleInfo(**sample_info_dna_raw)

    # THEN assert that rank_model_version was set
    assert sample_info_object.sv_rank_model_version == "v1.2.0"
