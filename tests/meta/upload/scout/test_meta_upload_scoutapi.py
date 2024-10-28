"""Tests for the scout upload API"""

from pathlib import Path

import pytest

from cg.io.yaml import read_yaml
from cg.meta.upload.scout.scout_config_builder import ScoutConfigBuilder
from cg.meta.upload.scout.uploadscoutapi import UploadScoutAPI
from cg.models.scout.scout_load_config import ScoutLoadConfig


def test_unlinked_family_is_linked(
    raredisease_config_builder: ScoutConfigBuilder, delivery_report_html: Path
):
    """Test that is_family check fails when samples are not linked"""
    # GIVEN a upload scout api and case data for a case without linked individuals
    family_data: ScoutLoadConfig = ScoutLoadConfig(
        **{
            "samples": [
                {"sample_id": "ADM2", "father": "0", "mother": "0"},
                {"sample_id": "ADM3", "father": "0", "mother": "0"},
            ],
            "delivery_report": delivery_report_html.as_posix(),
        }
    )
    # WHEN running the check if case is linked
    res = raredisease_config_builder.is_family_case(load_config=family_data)
    # THEN assert that the test returns False
    assert res is False


def test_family_is_linked(
    raredisease_config_builder: ScoutConfigBuilder, delivery_report_html: Path
):
    """Test that is_family returns true when samples are linked"""
    # GIVEN a upload scout api and case data for a linked case

    family_data: ScoutLoadConfig = ScoutLoadConfig(
        **{
            "samples": [
                {"sample_id": "ADM1", "father": "ADM2", "mother": "ADM3"},
                {"sample_id": "ADM2", "father": "0", "mother": "0"},
                {"sample_id": "ADM3", "father": "0", "mother": "0"},
            ],
            "delivery_report": delivery_report_html.as_posix(),
        }
    )
    # WHEN running the check if case is linked
    res = raredisease_config_builder.is_family_case(family_data)
    # THEN assert that the test returns True
    assert res is True


def test_save_config_creates_file(
    upload_scout_api: UploadScoutAPI, mip_load_config: ScoutLoadConfig, tmp_file
):
    """ "Tests that save config creates a file"""

    # GIVEN a scout_config object and a path to save it on

    # WHEN calling method to save config
    upload_scout_api.save_config_file(upload_config=mip_load_config, file_path=tmp_file)

    # THEN the config should exist on disk
    assert tmp_file.exists()


def test_save_config_creates_yaml(
    upload_scout_api: UploadScoutAPI, mip_load_config: ScoutLoadConfig, tmp_file: Path
):
    """Tests that the file created by save_config_file create a yaml"""

    # GIVEN a scout_config dict and a path to save it on

    # WHEN calling method to save config
    upload_scout_api.save_config_file(upload_config=mip_load_config, file_path=tmp_file)

    # THEN it is possible to read the file as yaml
    assert read_yaml(file_path=tmp_file)


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
