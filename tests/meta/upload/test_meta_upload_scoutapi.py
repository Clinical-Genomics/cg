"""Tests for the scout upload API"""
from pathlib import Path

import yaml

import pytest
from cg.apps.hk import HousekeeperAPI
from cg.meta.upload.scoutapi import UploadScoutAPI
from cg.store import Store


def test_unlinked_family_is_linked(upload_scout_api):
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


def test_generate_config_adds_rank_model_version(
    analysis: Store.Analysis, upload_scout_api: UploadScoutAPI
):
    # GIVEN a status db and hk with an analysis
    assert analysis

    # WHEN generating the scout config for the analysis
    result_data = upload_scout_api.generate_config(analysis)

    # THEN the config should contain the rank model version used
    assert result_data["human_genome_build"]
    assert result_data["rank_model_version"]


def test_generate_config_adds_vcf2cytosure(
    analysis: Store.Analysis, upload_scout_api: UploadScoutAPI
):
    # GIVEN a status db and hk with an analysis
    assert analysis

    # WHEN generating the scout config for the analysis
    result_data = upload_scout_api.generate_config(analysis)

    # THEN the config should contain the vcf2cytosure cgh file path on each sample
    for sample in result_data["samples"]:
        assert sample["vcf2cytosure"]


def _file_exists_on_disk(file_path: Path):
    """Returns if the file exists on disk"""
    return file_path.exists()


def _file_is_yaml(file_path):
    """Returns if the file successfully was loaded as yaml"""
    data = None
    with open(file_path, "r") as stream:
        try:
            data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            return False
    return data is not None


def test_save_config_creates_file(upload_scout_api: UploadScoutAPI, tmp_file):
    """"Tests that save config creates a file"""

    # GIVEN a scout_config dict and a path to save it on
    scout_config = {"dummy": "data"}

    # WHEN calling method to save config
    result_data = upload_scout_api.save_config_file(
        upload_config=scout_config, file_path=tmp_file
    )

    # THEN the config should exist on disk
    assert _file_exists_on_disk(tmp_file)


def test_save_config_creates_yaml(upload_scout_api: UploadScoutAPI, tmp_file):
    """Tests that the file created by save_config_file create a yaml """

    # GIVEN a scout_config dict and a path to save it on
    scout_config = {"dummy": "data"}

    # WHEN calling method to save config
    result_data = upload_scout_api.save_config_file(
        upload_config=scout_config, file_path=tmp_file
    )

    # THEN the should be of yaml type
    assert _file_is_yaml(tmp_file)


def test_add_scout_config_to_hk(
    upload_scout_api: UploadScoutAPI, housekeeper_api: HousekeeperAPI, tmp_file
):
    # GIVEN a hk_mock and a file path to scout load config
    # WHEN adding the file path to hk_api
    file_obj = upload_scout_api.add_scout_config_to_hk(
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
    # GIVEN a hk_mock with an scout upload file and a file path to scout load config
    housekeeper_api._files = ["a file path"]
    # WHEN adding the file path to hk_api
    with pytest.raises(FileExistsError):
        # THEN assert File exists exception is raised
        file_obj = upload_scout_api.add_scout_config_to_hk(
            config_file_path=tmp_file, hk_api=housekeeper_api, case_id="dummy"
        )
    # THEN assert file is not added to hk-db
    assert housekeeper_api._file_added is False
    # THEN assert file is not included in hk-db
    assert housekeeper_api._file_included is False
