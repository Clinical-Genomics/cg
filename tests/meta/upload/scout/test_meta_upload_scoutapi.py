"""Tests for the scout upload API"""
import logging
from pathlib import Path

import pytest
import yaml

from cg.apps.scout.scout_load_config import MipLoadConfig, ScoutLoadConfig, ScoutMipIndividual
from cg.meta.upload.scout.scoutapi import UploadScoutAPI
from cg.store import Store, models

CASE_FILE_PATHS = ["multiqc"]

RESULT_KEYS = [
    "family",
    "human_genome_build",
    "rank_model_version",
    "sv_rank_model_version",
]

SAMPLE_FILE_PATHS = ["alignment_path", "chromograph", "vcf2cytosure"]


def test_unlinked_family_is_linked(upload_scout_api: UploadScoutAPI):
    """Test that is_family check fails when samples are not linked"""
    # GIVEN a upload scout api and case data for a family without linked individuals
    family_data: MipLoadConfig = MipLoadConfig(
        **{
            "samples": [
                {"sample_id": "ADM2", "father": "0", "mother": "0"},
                {"sample_id": "ADM3", "father": "0", "mother": "0"},
            ]
        }
    )
    # WHEN running the check if family is linked
    res = upload_scout_api._is_family_case(family_data)
    # THEN assert that the test returns False
    assert res is False


def test_family_is_linked(upload_scout_api: UploadScoutAPI):
    """Test that is_family returns true when samples are linked"""
    # GIVEN a upload scout api and case data for a linked family
    family_data: MipLoadConfig = MipLoadConfig(
        **{
            "samples": [
                {"sample_id": "ADM1", "father": "ADM2", "mother": "ADM3"},
                {"sample_id": "ADM2", "father": "0", "mother": "0"},
                {"sample_id": "ADM3", "father": "0", "mother": "0"},
            ]
        }
    )
    # WHEN running the check if family is linked
    res = upload_scout_api._is_family_case(family_data)
    # THEN assert that the test returns True
    assert res is True


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


def _file_exists_on_disk(file_path: Path):
    """Returns if the file exists on disk"""
    return file_path.exists()


def _file_is_yaml(file_path):
    """Returns if the file successfully was loaded as yaml"""
    data = None
    with open(file_path, "r") as stream:
        try:
            data = yaml.safe_load(stream)
        except yaml.YAMLError:
            return False
    return data is not None


def test_save_config_creates_file(
    upload_scout_api: UploadScoutAPI, mip_load_config: ScoutLoadConfig, tmp_file
):
    """"Tests that save config creates a file"""

    # GIVEN a scout_config object and a path to save it on

    # WHEN calling method to save config
    upload_scout_api.save_config_file(upload_config=mip_load_config, file_path=tmp_file)

    # THEN the config should exist on disk
    assert _file_exists_on_disk(tmp_file)


def test_save_config_creates_yaml(
    upload_scout_api: UploadScoutAPI, mip_load_config: ScoutLoadConfig, tmp_file
):
    """Tests that the file created by save_config_file create a yaml """

    # GIVEN a scout_config dict and a path to save it on

    # WHEN calling method to save config
    upload_scout_api.save_config_file(upload_config=mip_load_config, file_path=tmp_file)

    # THEN the should be of yaml type
    assert _file_is_yaml(tmp_file)


def test_add_scout_config_to_hk(upload_scout_api: UploadScoutAPI, tmp_file):
    """Test that scout load config is added to housekeeper"""
    # GIVEN a hk_mock and a file path to scout load config
    tag_name = UploadScoutAPI.get_load_config_tag()
    housekeeper_api = upload_scout_api.housekeeper
    # GIVEN a hk mock that does not return a config file
    housekeeper_api.add_missing_tag(tag_name)
    # WHEN adding the file path to hk_api

    upload_scout_api.add_scout_config_to_hk(config_file_path=tmp_file, case_id="dummy")
    # THEN assert that the file path is added to hk
    # file added to hk-db
    assert housekeeper_api.is_file_added() is True
    assert housekeeper_api.is_file_included() is True


def test_add_scout_config_to_hk_existing_files(upload_scout_api: UploadScoutAPI, tmp_file):
    """Test that scout config is not updated in housekeeper if it already exists"""
    # GIVEN a hk_mock with an scout upload file and a file path to scout load config
    housekeeper_api = upload_scout_api.housekeeper
    # GIVEN that there are files in the hk mock
    housekeeper_api.new_file(tmp_file.name)
    assert housekeeper_api.files
    # WHEN adding the file path to hk_api
    with pytest.raises(FileExistsError):
        # THEN assert File exists exception is raised
        upload_scout_api.add_scout_config_to_hk(config_file_path=tmp_file, case_id="dummy")
