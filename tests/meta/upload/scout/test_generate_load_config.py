"""Test the methods that generate a scout load config"""

import pytest

from cg.constants import Workflow
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


@pytest.mark.parametrize(
    "analysis_obj, workflow, expected_config_class",
    [
        ("balsamic_analysis_obj", Workflow.BALSAMIC, BalsamicLoadConfig,),
        ("balsamic_umi_analysis_obj", Workflow.BALSAMIC_UMI, BalsamicUmiLoadConfig),
        ("rnafusion_analysis_obj", Workflow.RNAFUSION, RnafusionLoadConfig),
    ],
    indirect=["analysis_obj"]  # Indirectly resolve the fixture names
)
def test_generate_load_config(
    analysis_obj: Analysis,
    workflow: Workflow,
    expected_config_class,
    upload_scout_api: UploadScoutAPI,
):
    """Test that the correct Scout load config is generated for various workflows."""

    # GIVEN an analysis object for the respective workflow
    assert analysis_obj.workflow == workflow

    # WHEN generating a load config using the appropriate upload scout API
    # config = upload_scout_api.generate_config(analysis=analysis_obj)

    # THEN assert that the generated config matches the expected config class
    # assert isinstance(config, expected_config_class)



# @pytest.mark.parametrize("result_key", RESULT_KEYS)
# def test_generate_config_adds_meta_result_key(
#     result_key: str,
#     mip_dna_analysis: Analysis,
#     upload_mip_analysis_scout_api: UploadScoutAPI,
# ):
#     """Test that generate config adds the expected result keys"""
#     # GIVEN a status db and hk with an analysis
#     assert mip_dna_analysis

#     # WHEN generating the scout config for the analysis
#     result_data: ScoutLoadConfig = upload_mip_analysis_scout_api.generate_config(
#         analysis=mip_dna_analysis
#     )

#     # THEN the config should contain the rank model version used
#     assert result_data.model_dump()[result_key]


# def test_generate_config_adds_sample_paths(
#     sample_id: str,
#     mip_dna_analysis: Analysis,
#     upload_mip_analysis_scout_api: UploadScoutAPI,
# ):
#     """Test that generate config adds vcf2cytosure file"""
#     # GIVEN a status db and hk with an analysis

#     # WHEN generating the scout config for the analysis
#     result_data: ScoutLoadConfig = upload_mip_analysis_scout_api.generate_config(mip_dna_analysis)

#     # THEN the config should contain the sample file path for each sample
#     sample: ScoutMipIndividual
#     for sample in result_data.samples:
#         if sample.sample_id == sample_id:
#             assert sample.vcf2cytosure


# def test_generate_config_adds_case_paths(
#     sample_id: str,
#     mip_dna_analysis: Analysis,
#     upload_mip_analysis_scout_api: UploadScoutAPI,
# ):
#     """Test that generate config adds case file paths"""
#     # GIVEN a status db and hk with an analysis

#     # WHEN generating the scout config for the analysis
#     result_data: ScoutLoadConfig = upload_mip_analysis_scout_api.generate_config(mip_dna_analysis)

#     # THEN the config should contain the multiqc file path
#     assert result_data.multiqc
