"""Test ObservationsInputFiles pydantic model behaviour."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from cg.models.observations.input_files import (
    BalsamicObservationsInputFiles,
    MipDNAObservationsInputFiles,
    RarediseaseObservationsInputFiles,
)


def test_instantiate_input_files(mip_dna_observations_input_files_raw: dict[str, Path]):
    """Tests input files against a pydantic MipDNAObservationsInputFiles."""

    # GIVEN a dictionary with the basic input files

    # WHEN instantiating an observations input files object
    input_files = MipDNAObservationsInputFiles(**mip_dna_observations_input_files_raw)

    # THEN assert that it was successfully created
    assert isinstance(input_files, MipDNAObservationsInputFiles)


def test_instantiate_input_files_missing_field(
    mip_dna_observations_input_files_raw: dict[str, Path], file_does_not_exist: Path
):
    """Tests input files against a pydantic MipDNAObservationsInputFiles with not existent field."""

    # GIVEN a dictionary with the basic input files and a file path that does not exist
    mip_dna_observations_input_files_raw["snv_vcf_path"] = file_does_not_exist

    # WHEN checking the observation file

    # THEN the file is not successfully validated and an error is returned
    with pytest.raises(ValidationError):
        # WHEN instantiating a ObservationsInputFiles object
        MipDNAObservationsInputFiles(**mip_dna_observations_input_files_raw)


def test_instantiate_balsamic_input_files(balsamic_observations_input_files_raw: dict[str, Path]):
    """Tests input files against a pydantic BalsamicObservationsInputFiles."""

    # GIVEN balsamic input files

    # WHEN instantiating an observations input files object
    input_files = BalsamicObservationsInputFiles(**balsamic_observations_input_files_raw)

    # THEN assert that it was successfully created
    assert isinstance(input_files, BalsamicObservationsInputFiles)


def test_instantiate_balsamic_input_files_missing_field(
    balsamic_observations_input_files_raw: dict[str, Path], file_does_not_exist: Path
):
    """Tests input files against a pydantic BalsamicObservationsInputFiles with not existent field."""

    # GIVEN a dictionary with the basic input files and a file path that does not exist
    balsamic_observations_input_files_raw["snv_germline_vcf_path"] = file_does_not_exist

    # WHEN checking the observation file

    # THEN the file is not successfully validated and an error is returned
    with pytest.raises(ValidationError):
        # WHEN instantiating a ObservationsInputFiles object
        BalsamicObservationsInputFiles(**balsamic_observations_input_files_raw)


def test_instantiate_raredisease_input_files(
    raredisease_observations_input_files_raw: dict[str, Path]
):
    """Tests input files against a pydantic RarediseaseObservationsInputFiles."""

    # GIVEN RAREDISEASE input files

    # WHEN instantiating an observations input files object
    input_files = RarediseaseObservationsInputFiles(**raredisease_observations_input_files_raw)

    # THEN assert that it was successfully created
    assert isinstance(input_files, RarediseaseObservationsInputFiles)


def test_instantiate_raredisease_input_files_missing_field(
    raredisease_observations_input_files_raw: dict[str, Path], file_does_not_exist: Path
):
    """Tests input files against a pydantic RarediseaseObservationsInputFiles with not existent field."""

    # GIVEN a dictionary with the basic input files and a file path that does not exist
    raredisease_observations_input_files_raw["snv_vcf_path"] = file_does_not_exist

    # WHEN checking the observation file

    # THEN the file is not successfully validated and an error is returned
    with pytest.raises(ValidationError):
        # WHEN instantiating a ObservationsInputFiles object
        RarediseaseObservationsInputFiles(**raredisease_observations_input_files_raw)
