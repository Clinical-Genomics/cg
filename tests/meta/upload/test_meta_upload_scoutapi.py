"""Tests for the scout upload API"""
from pathlib import Path

import pytest
import yaml

from cg.apps.hk import HousekeeperAPI
from cg.meta.upload.scoutapi import UploadScoutAPI
from cg.store import Store


def test_unlinked_family_is_linked(upload_scout_api):
    """Test that is_family check fails when samples are not linked"""
    # GIVEN a upload scout api and case data for a family without linked individuals
    family_data = {
        "samples": [
            {"sample_id": "ADM2", "father": "0", "mother": "0"},
            {"sample_id": "ADM3", "father": "0", "mother": "0"},
        ]
    }
    # WHEN running the check if family is linked
    res = upload_scout_api._is_family_case(family_data)
    # THEN assert that the test returns False
    assert res is False


def test_family_is_linked(upload_scout_api):
    """Test that is_family returns true when samples are linked"""
    # GIVEN a upload scout api and case data for a linked family
    family_data = {
        "samples": [
            {"sample_id": "ADM1", "father": "ADM2", "mother": "ADM3"},
            {"sample_id": "ADM2", "father": "0", "mother": "0"},
            {"sample_id": "ADM3", "father": "0", "mother": "0"},
        ]
    }
    # WHEN running the check if family is linked
    res = upload_scout_api._is_family_case(family_data)
    # THEN assert that the test returns True
    assert res is True


result_keys = [
    "family",
    "human_genome_build",
    "rank_model_version",
    "sv_rank_model_version",
]


@pytest.mark.parametrize("result_key", result_keys)
def test_generate_config_adds_meta_result_key(
    result_key, analysis: Store.Analysis, upload_scout_api: UploadScoutAPI
):
    """Test that generate config adds rank model version"""
    # GIVEN a status db and hk with an analysis
    assert analysis  # WHEN generating the scout config for the analysis
    result_data = upload_scout_api.generate_config(
        analysis
    )  # THEN the config should contain the rank model version used
    assert result_data[result_key]


sample_file_paths = ["chromograph", "vcf2cytosure"]


@pytest.mark.parametrize("file_path", sample_file_paths)
def test_generate_config_adds_sample_paths(
    file_path, analysis: Store.Analysis, upload_scout_api: UploadScoutAPI
):
    """Test that generate config adds vcf2cytosure file"""
    # GIVEN a status db and hk with an analysis
    assert analysis

    # WHEN generating the scout config for the analysis
    result_data = upload_scout_api.generate_config(analysis)

    # THEN the config should contain the sample file path for each sample
    for sample in result_data["samples"]:
        assert sample[file_path]


case_file_paths = ["multiqc"]


@pytest.mark.parametrize("file_path", case_file_paths)
def test_generate_config_adds_sample_paths(
    file_path, analysis: Store.Analysis, upload_scout_api: UploadScoutAPI
):
    """Test that generate config adds case file paths"""
    # GIVEN a status db and hk with an analysis
    assert analysis

    # WHEN generating the scout config for the analysis
    result_data = upload_scout_api.generate_config(analysis)

    # THEN the config should contain the case file path
    assert result_data[file_path]


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


def test_save_config_creates_file(upload_scout_api: UploadScoutAPI, tmp_file):
    """"Tests that save config creates a file"""

    # GIVEN a scout_config dict and a path to save it on
    scout_config = {"dummy": "data"}

    # WHEN calling method to save config
    upload_scout_api.save_config_file(upload_config=scout_config, file_path=tmp_file)

    # THEN the config should exist on disk
    assert _file_exists_on_disk(tmp_file)


def test_save_config_creates_yaml(upload_scout_api: UploadScoutAPI, tmp_file):
    """Tests that the file created by save_config_file create a yaml """

    # GIVEN a scout_config dict and a path to save it on
    scout_config = {"dummy": "data"}

    # WHEN calling method to save config
    upload_scout_api.save_config_file(upload_config=scout_config, file_path=tmp_file)

    # THEN the should be of yaml type
    assert _file_is_yaml(tmp_file)


def test_add_scout_config_to_hk(
    upload_scout_api: UploadScoutAPI, housekeeper_api: HousekeeperAPI, tmp_file
):
    """Test that scout load config is added to housekeeper"""
    # GIVEN a hk_mock and a file path to scout load config
    # WHEN adding the file path to hk_api
    upload_scout_api.add_scout_config_to_hk(
        config_file_path=tmp_file, hk_api=housekeeper_api, case_id="dummy"
    )
    # THEN assert that the file path is added to hk
    # file added to hk-db
    assert housekeeper_api._file_added is True
    # file linked to hk-disk
    assert housekeeper_api._file_included is True


def test_add_scout_config_to_hk_existing_files(
    upload_scout_api: UploadScoutAPI, housekeeper_api: HousekeeperAPI, tmp_file
):
    """Test that scout config is not updated in housekeeper if it already exists"""
    # GIVEN a hk_mock with an scout upload file and a file path to scout load config
    housekeeper_api._files = ["a file path"]
    # WHEN adding the file path to hk_api
    with pytest.raises(FileExistsError):
        # THEN assert File exists exception is raised
        upload_scout_api.add_scout_config_to_hk(
            config_file_path=tmp_file, hk_api=housekeeper_api, case_id="dummy"
        )
    # THEN assert file is not added to hk-db
    assert housekeeper_api._file_added is False
    # THEN assert file is not included in hk-db
    assert housekeeper_api._file_included is False
