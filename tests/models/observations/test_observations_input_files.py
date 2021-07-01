from pathlib import Path

import pytest

from cg.models.observations.observations_input_files import (
    ObservationsInputFiles,
    check_observation_file_from_hk,
)


def test_instantiate_input_files(observation_input_files_raw: dict):
    """Tests input files against a pydantic ObservationsInputFiles"""
    # GIVEN a dictionary with the basic config

    # WHEN instantiating a MipBaseConfig object
    files_object = ObservationsInputFiles(**observation_input_files_raw)

    # THEN assert that it was successfully created
    assert isinstance(files_object, ObservationsInputFiles)


def test_input_files_case_id(case_id: str, observation_input_files_raw: dict):
    """Test case_id"""
    # GIVEN a dictionary with the basic input files

    # WHEN instantiating a ObservationsInputFiles object
    files_object = ObservationsInputFiles(**observation_input_files_raw)

    # THEN assert that case_id was set
    assert files_object.case_id == case_id


def test_check_observation_file_from_hk(filled_file: Path, hk_tag: str):
    """Test check_observation_file_from_hk"""
    # GIVEN a file path which exists

    # GIVEN a Housekeeper tag

    # WHEN checking the observation file
    is_ok = check_observation_file_from_hk(file_tag=hk_tag, file=filled_file)

    # THEN if file is ok return true
    assert is_ok


def test_check_observation_file_from_hk_when_no_hk_file_exists(hk_tag: str):
    """Test check_observation_file_from_hk when file does not exist"""
    # GIVEN a file path which is None
    file = None

    # GIVEN a Housekeeper tag

    with pytest.raises(FileNotFoundError):
        # WHEN checking the observation file

        # THEN FileNotFoundError should be raised
        check_observation_file_from_hk(file_tag=hk_tag, file=file)


def test_check_observation_file_from_hk_when_file_not_exists(
    file_does_not_exist: Path, hk_tag: str
):
    """Test check_observation_file_from_hk when file does not exist"""
    # GIVEN a file path which does not exists

    # GIVEN a Housekeeper tag

    # THEN check that file does not exit
    assert file_does_not_exist.exists() is False

    with pytest.raises(FileNotFoundError):
        # WHEN checking the observation file

        # THEN FileNotFoundError should be raised
        check_observation_file_from_hk(file_tag=hk_tag, file=file_does_not_exist)


def test_input_files_pedigree(filled_file: Path, observation_input_files_raw: dict):
    """Test pedigree validator"""
    # GIVEN a dictionary with the basic input files

    # WHEN instantiating a ObservationsInputFiles object
    files_object = ObservationsInputFiles(**observation_input_files_raw)

    # THEN assert that pedigree file was set
    assert files_object.pedigree == filled_file


def test_input_files_pedigree_not_exists(
    file_does_not_exist: Path, observation_input_files_raw: dict
):
    """Test pedigree validator when file does not exits"""
    # GIVEN a dictionary with the basic input files

    # WHEN pedigree file does not exist in file system
    observation_input_files_raw["pedigree"] = file_does_not_exist

    assert Path(observation_input_files_raw["pedigree"]).exists() is False

    with pytest.raises(FileNotFoundError):
        # WHEN instantiating a ObservationsInputFiles object
        files_object = ObservationsInputFiles(**observation_input_files_raw)

        assert files_object.pedigree.exists() is False


def test_input_files_sv_vcf_when_none(observation_input_files_raw: dict):
    """Test sv_vcf validator when file is None"""
    # GIVEN a dictionary with the basic input files

    # WHEN instantiating a ObservationsInputFiles object
    files_object = ObservationsInputFiles(**observation_input_files_raw)

    assert files_object.sv_vcf is None


def test_input_files_sv_vcf_when_file(filled_file: Path, observation_input_files_raw: dict):
    """Test sv_vcf validator when file is supplied and exists"""
    # GIVEN a dictionary with the basic input files

    # GIVEN a sv_vcf file path
    observation_input_files_raw["sv_vcf"] = filled_file

    # WHEN instantiating a ObservationsInputFiles object
    files_object = ObservationsInputFiles(**observation_input_files_raw)

    assert files_object.sv_vcf == filled_file
