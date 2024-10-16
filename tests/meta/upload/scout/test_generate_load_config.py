"""Test the methods that generate a scout load config"""

import pytest

from cg.constants import Workflow
from cg.meta.upload.scout.mip_config_builder import MipConfigBuilder
from cg.meta.upload.scout.uploadscoutapi import UploadScoutAPI
from cg.models.scout.scout_load_config import (
    BalsamicLoadConfig,
    BalsamicUmiLoadConfig,
    MipLoadConfig,
    RarediseaseLoadConfig,
    RnafusionLoadConfig,
    ScoutLoadConfig,
    ScoutMipIndividual,
)
from cg.store.models import Analysis

RESULT_KEYS = [
    "family",
    "human_genome_build",
    "rank_model_version",
    "sv_rank_model_version",
]

RESULT_KEYS_RD = [
    "family",
    "human_genome_build",
]

SAMPLE_FILE_PATHS = ["alignment_path", "chromograph", "vcf2cytosure"]


def test_add_mandatory_info_to_mip_config(mip_config_builder: MipConfigBuilder):

    load_config = MipLoadConfig()
    # GIVEN an cg analysis object

    # GIVEN a mip load config object
    assert load_config.owner is None
    # GIVEN a file handler with some housekeeper version data

    # WHEN adding the mandatory information
    mip_config_builder.add_common_info_to_load_config(load_config)

    # THEN assert mandatory field owner was set
    assert load_config.owner


def test_generate_balsamic_load_config(
    balsamic_analysis_obj: Analysis, upload_balsamic_analysis_scout_api: UploadScoutAPI
):
    # GIVEN an analysis object that have been run with balsamic
    assert balsamic_analysis_obj.workflow == Workflow.BALSAMIC

    # GIVEN an upload scout api with some balsamic information

    # WHEN generating a load config
    config = upload_balsamic_analysis_scout_api.generate_config(analysis=balsamic_analysis_obj)

    # THEN assert that the config is a balsamic config
    assert isinstance(config, BalsamicLoadConfig)


def test_generate_balsamic_umi_load_config(
    balsamic_umi_analysis_obj: Analysis, upload_balsamic_analysis_scout_api: UploadScoutAPI
):
    # GIVEN an analysis object that have been run with balsamic-umi
    assert balsamic_umi_analysis_obj.workflow == Workflow.BALSAMIC_UMI

    # GIVEN an upload scout api with some balsamic information

    # WHEN generating a load config
    config = upload_balsamic_analysis_scout_api.generate_config(analysis=balsamic_umi_analysis_obj)

    # THEN assert that the config is a balsamic-umi config
    assert isinstance(config, BalsamicUmiLoadConfig)


def test_generate_mip_load_config(
    mip_dna_analysis: Analysis, upload_mip_analysis_scout_api: UploadScoutAPI
):
    """Test that a RAREDISEASE config is generated."""
    # GIVEN an analysis object that have been run with RAREDISEASE
    assert mip_dna_analysis.workflow == Workflow.MIP_DNA

    # GIVEN an upload scout api with some RAREDISEASE information
    # WHEN generating a load config
    config = upload_mip_analysis_scout_api.generate_config(analysis=mip_dna_analysis)

    # THEN assert that the config is a balsamic config
    assert isinstance(config, MipLoadConfig)


def test_generate_raredisease_load_config(
    raredisease_analysis_obj: Analysis, upload_raredisease_analysis_scout_api: UploadScoutAPI
):
    """Test that a RAREDISEASE config is generated."""
    # GIVEN an analysis object that have been run with RAREDISEASE
    assert raredisease_analysis_obj.workflow == Workflow.RAREDISEASE

    # GIVEN an upload scout api with some RAREDISEASE information
    # WHEN generating a load config
    config = upload_raredisease_analysis_scout_api.generate_config(
        analysis=raredisease_analysis_obj
    )

    # THEN assert that the config is a balsamic config
    assert isinstance(config, RarediseaseLoadConfig)


def test_generate_rnafusion_load_config(
    rnafusion_analysis_obj: Analysis, upload_rnafusion_analysis_scout_api: UploadScoutAPI
):
    """Test that a rnafusion config is generated."""
    # GIVEN an analysis object that have been run with rnafusion
    assert rnafusion_analysis_obj.workflow == Workflow.RNAFUSION

    # GIVEN an upload scout api with some rnafusion information

    # WHEN generating a load config
    config = upload_rnafusion_analysis_scout_api.generate_config(analysis=rnafusion_analysis_obj)

    # THEN assert that the config is a rnafusion config
    assert isinstance(config, RnafusionLoadConfig)


@pytest.mark.parametrize("result_key", RESULT_KEYS)
def test_generate_config_adds_meta_result_key_mip(
    result_key: str,
    mip_dna_analysis: Analysis,
    upload_mip_analysis_scout_api: UploadScoutAPI,
):
    """Test that generate config adds the expected result keys"""
    # GIVEN a status db and hk with an analysis
    assert mip_dna_analysis

    # WHEN generating the scout config for the analysis
    result_data: MipLoadConfig = upload_mip_analysis_scout_api.generate_config(
        analysis=mip_dna_analysis
    )

    # THEN the config should contain the rank model version used
    assert getattr(result_data, result_key) is not None


@pytest.mark.parametrize("result_key", RESULT_KEYS_RD)
def test_generate_config_adds_meta_result_key_raredisease(
    result_key: str,
    raredisease_analysis_obj: Analysis,
    upload_raredisease_analysis_scout_api: UploadScoutAPI,
):
    """Test that generate config adds the expected result keys"""
    # GIVEN a status db and hk with an analysis
    assert raredisease_analysis_obj

    # WHEN generating the scout config for the analysis
    result_data: RarediseaseLoadConfig = upload_raredisease_analysis_scout_api.generate_config(
        analysis=raredisease_analysis_obj
    )

    # THEN the config should contain the rank model version used
    assert getattr(result_data, result_key) is not None


def test_generate_config_adds_sample_paths_mip(
    sample_id: str,
    mip_dna_analysis: Analysis,
    upload_mip_analysis_scout_api: UploadScoutAPI,
):
    """Test that generate config adds vcf2cytosure file"""
    # GIVEN a status db and hk with an analysis

    # WHEN generating the scout config for the analysis
    result_data: MipLoadConfig = upload_mip_analysis_scout_api.generate_config(
        analysis=mip_dna_analysis
    )

    # THEN the config should contain the sample file path for each sample
    sample: ScoutMipIndividual
    for sample in result_data.samples:
        if sample.sample_id == sample_id:
            assert sample.vcf2cytosure


def test_generate_config_adds_sample_paths_raredisease(
    sample_id: str,
    raredisease_analysis_obj: Analysis,
    upload_raredisease_analysis_scout_api: UploadScoutAPI,
):
    """Test that generate config adds vcf2cytosure file"""
    # GIVEN a status db and hk with an analysis

    # WHEN generating the scout config for the analysis
    result_data: MipLoadConfig = upload_raredisease_analysis_scout_api.generate_config(
        raredisease_analysis_obj
    )

    # THEN the config should contain the sample file path for each sample
    sample: ScoutMipIndividual
    for sample in result_data.samples:
        if sample.sample_id == sample_id:
            assert sample.vcf2cytosure


def test_generate_config_adds_case_paths_mip(
    sample_id: str,
    mip_dna_analysis: Analysis,
    upload_mip_analysis_scout_api: UploadScoutAPI,
):
    """Test that generate config adds case file paths"""
    # GIVEN a status db and hk with an analysis

    # WHEN generating the scout config for the analysis
    result_data: MipLoadConfig = upload_mip_analysis_scout_api.generate_config(mip_dna_analysis)

    # THEN the config should contain the multiqc file path
    assert result_data.multiqc
