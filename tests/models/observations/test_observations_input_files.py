"""Test ObservationsInputFiles pydantic model behaviour."""

from pathlib import Path

import pytest

from cg.models.observations.input_files import (
    MipDNAObservationsInputFiles,
    validate_observations_file,
)


def test_instantiate_input_files(mip_dna_observation_input_files: dict):
    """Tests input files against a pydantic MipDNAObservationsInputFiles."""

    # GIVEN a dictionary with the basic input files

    # WHEN instantiating an observations input files object
    input_files = MipDNAObservationsInputFiles(**mip_dna_observation_input_files)

    # THEN assert that it was successfully created
    assert isinstance(input_files, MipDNAObservationsInputFiles)


def test_instantiate_input_files_missing_field(
    mip_dna_observation_input_files: dict, file_does_not_exist: Path
):
    """Tests input files against a pydantic MipDNAObservationsInputFiles with not existent field."""

    # GIVEN a dictionary with the basic input files and a file path that does not exist
    mip_dna_observation_input_files["vcf_path"] = file_does_not_exist

    # WHEN checking the observation file

    # THEN the file is not successfully validated and an error is returned
    with pytest.raises(FileNotFoundError):
        # WHEN instantiating a ObservationsInputFiles object
        MipDNAObservationsInputFiles(**mip_dna_observation_input_files)


def test_input_files_case_id(case_id: str, mip_dna_observation_input_files: dict):
    """Test case ID assignment."""

    # GIVEN a dictionary with the basic input files

    # WHEN instantiating an observations input files object
    files_object = MipDNAObservationsInputFiles(**mip_dna_observation_input_files)

    # THEN assert that case ID was set
    assert files_object.case_id == case_id


def test_validate_observations_file(filled_file: Path):
    """Test observations file validation method."""

    # GIVEN a file path

    # WHEN checking the observation file
    observations_file = validate_observations_file(filled_file)

    # THEN the file is successfully validated and returned
    assert observations_file


def test_validate_observations_file_when_no_exists(file_does_not_exist: Path):
    """Test observations file validation method when file does not exist."""

    # GIVEN a file path that does not exist

    # WHEN checking the observation file

    # THEN the file is not successfully validated and an error is returned
    with pytest.raises(FileNotFoundError):
        validate_observations_file(file_does_not_exist)
