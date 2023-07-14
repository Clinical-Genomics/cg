"""Test the methods that generate a scout load config"""

import pytest

from cg.constants import Pipeline
from cg.meta.upload.scout.mip_config_builder import MipConfigBuilder
from cg.meta.upload.scout.uploadscoutapi import UploadScoutAPI
from cg.models.scout.scout_load_config import (
    BalsamicLoadConfig,
    BalsamicUmiLoadConfig,
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

SAMPLE_FILE_PATHS = ["alignment_path", "chromograph", "vcf2cytosure"]


def test_add_mandatory_info_to_mip_config(
    analysis_obj: Analysis, mip_config_builder: MipConfigBuilder
):
    # GIVEN an cg analysis object

    # GIVEN a mip load config object
    assert mip_config_builder.load_config.owner is None
    # GIVEN a file handler with some housekeeper version data

    # WHEN adding the mandatory information
    mip_config_builder.add_common_info_to_load_config()

    # THEN assert mandatory field owner was set
    assert mip_config_builder.load_config.owner


def test_generate_balsamic_load_config(
    balsamic_analysis_obj: Analysis, upload_balsamic_analysis_scout_api: UploadScoutAPI
):
    # GIVEN an analysis object that have been run with balsamic
    assert balsamic_analysis_obj.pipeline == Pipeline.BALSAMIC

    # GIVEN an upload scout api with some balsamic information

    # WHEN generating a load config
    config = upload_balsamic_analysis_scout_api.generate_config(analysis_obj=balsamic_analysis_obj)

    # THEN assert that the config is a balsamic config
    assert isinstance(config, BalsamicLoadConfig)


def test_generate_balsamic_umi_load_config(
    balsamic_umi_analysis_obj: Analysis, upload_balsamic_analysis_scout_api: UploadScoutAPI
):
    # GIVEN an analysis object that have been run with balsamic-umi
    assert balsamic_umi_analysis_obj.pipeline == Pipeline.BALSAMIC_UMI

    # GIVEN an upload scout api with some balsamic information

    # WHEN generating a load config
    config = upload_balsamic_analysis_scout_api.generate_config(
        analysis_obj=balsamic_umi_analysis_obj
    )

    # THEN assert that the config is a balsamic-umi config
    assert isinstance(config, BalsamicUmiLoadConfig)


def test_generate_rnafusion_load_config(
    rnafusion_analysis_obj: Analysis, upload_rnafusion_analysis_scout_api: UploadScoutAPI
):
    """Test that a rnafusion config is generated."""
    # GIVEN an analysis object that have been run with rnafusion
    assert rnafusion_analysis_obj.pipeline == Pipeline.RNAFUSION

    # GIVEN an upload scout api with some rnafusion information

    # WHEN generating a load config
    config: ScoutLoadConfig = upload_rnafusion_analysis_scout_api.generate_config(
        analysis_obj=rnafusion_analysis_obj
    )

    # THEN assert that the config is a rnafusion config
    assert isinstance(config, RnafusionLoadConfig)


@pytest.mark.parametrize("result_key", RESULT_KEYS)
def test_generate_config_adds_meta_result_key(
    result_key: str,
    mip_dna_analysis: Analysis,
    upload_mip_analysis_scout_api: UploadScoutAPI,
):
    """Test that generate config adds the expected result keys"""
    # GIVEN a status db and hk with an analysis
    assert mip_dna_analysis

    # WHEN generating the scout config for the analysis
    result_data: ScoutLoadConfig = upload_mip_analysis_scout_api.generate_config(
        analysis_obj=mip_dna_analysis
    )

    # THEN the config should contain the rank model version used
    assert result_data.dict()[result_key]


def test_generate_config_adds_sample_paths(
    sample_id: str,
    mip_dna_analysis: Analysis,
    upload_mip_analysis_scout_api: UploadScoutAPI,
):
    """Test that generate config adds vcf2cytosure file"""
    # GIVEN a status db and hk with an analysis

    # WHEN generating the scout config for the analysis
    result_data: ScoutLoadConfig = upload_mip_analysis_scout_api.generate_config(mip_dna_analysis)

    # THEN the config should contain the sample file path for each sample
    sample: ScoutMipIndividual
    for sample in result_data.samples:
        if sample.sample_id == sample_id:
            assert sample.vcf2cytosure


def test_generate_config_adds_case_paths(
    sample_id: str,
    mip_dna_analysis: Analysis,
    upload_mip_analysis_scout_api: UploadScoutAPI,
):
    """Test that generate config adds case file paths"""
    # GIVEN a status db and hk with an analysis

    # WHEN generating the scout config for the analysis
    result_data: ScoutLoadConfig = upload_mip_analysis_scout_api.generate_config(mip_dna_analysis)

    # THEN the config should contain the multiqc file path
    assert result_data.multiqc
