"""Test the methods that generate a scout load config"""

import pytest
from cg.constants import Pipeline
from cg.meta.upload.scout.mip_config_builder import MipConfigBuilder
from cg.meta.upload.scout.scout_load_config import (
    BalsamicLoadConfig,
    MipLoadConfig,
    ScoutLoadConfig,
    ScoutMipIndividual,
)
from cg.meta.upload.scout.scoutapi import UploadScoutAPI
from cg.store import Store, models

RESULT_KEYS = [
    "family",
    "human_genome_build",
    "rank_model_version",
    "sv_rank_model_version",
]

SAMPLE_FILE_PATHS = ["alignment_path", "chromograph", "vcf2cytosure"]


def test_add_mandatory_info_to_mip_config(
    analysis_obj: models.Analysis, mip_config_builder: MipConfigBuilder
):
    # GIVEN an cg analysis object
    # GIVEN a mip load config object
    assert mip_config_builder.load_config.owner is None
    # GIVEN a file handler with some housekeeper version data

    # WHEN adding the mandatory information
    mip_config_builder.add_mandatory_info_to_load_config()

    # THEN assert mandatory field owner was set
    assert mip_config_builder.load_config.owner


def test_generate_balsamic_load_config(
    balsamic_analysis_obj: models.Analysis, upload_balsamic_analysis_scout_api: UploadScoutAPI
):
    # GIVEN a analysis object that have been run with balsamic
    assert balsamic_analysis_obj.pipeline == Pipeline.BALSAMIC

    # GIVEN a upload scout api with some balsamic information

    # WHEN generating a load config
    config = upload_balsamic_analysis_scout_api.generate_config(analysis_obj=balsamic_analysis_obj)

    # THEN assert that the config is a balsamic config
    assert isinstance(config, BalsamicLoadConfig)


@pytest.mark.parametrize("result_key", RESULT_KEYS)
def test_generate_config_adds_meta_result_key(
    result_key: str,
    mip_analysis_obj: models.Analysis,
    upload_mip_analysis_scout_api: UploadScoutAPI,
):
    """Test that generate config adds the expected result keys"""
    # GIVEN a status db and hk with an analysis
    assert mip_analysis_obj

    # WHEN generating the scout config for the analysis
    result_data: ScoutLoadConfig = upload_mip_analysis_scout_api.generate_config(
        analysis_obj=mip_analysis_obj
    )

    # THEN the config should contain the rank model version used
    assert result_data.dict()[result_key]


def test_generate_config_adds_sample_paths(
    sample_id: str, mip_analysis_obj: models.Analysis, upload_mip_analysis_scout_api: UploadScoutAPI
):
    """Test that generate config adds vcf2cytosure file"""
    # GIVEN a status db and hk with an analysis

    # WHEN generating the scout config for the analysis
    result_data: ScoutLoadConfig = upload_mip_analysis_scout_api.generate_config(mip_analysis_obj)

    # THEN the config should contain the sample file path for each sample
    sample: ScoutMipIndividual
    for sample in result_data.samples:
        if sample.sample_id == sample_id:
            assert sample.vcf2cytosure


def test_generate_config_adds_case_paths(
    sample_id: str, mip_analysis_obj: Store.Analysis, upload_mip_analysis_scout_api: UploadScoutAPI
):
    """Test that generate config adds case file paths"""
    # GIVEN a status db and hk with an analysis

    # WHEN generating the scout config for the analysis
    result_data: ScoutLoadConfig = upload_mip_analysis_scout_api.generate_config(mip_analysis_obj)

    # THEN the config should contain the multiqc file path
    assert result_data.multiqc
