"""ObservationsInputFiles test fixtures."""

from pathlib import Path

import pytest

from cg.models.observations.input_files import (
    MipDNAObservationsInputFiles,
    BalsamicObservationsInputFiles,
)


@pytest.fixture(name="observations_input_files_raw")
def fixture_observations_input_files_raw(case_id: str, filled_file: Path) -> dict:
    """Return raw observations input files for rare diseases."""
    return {
        "snv_vcf_path": filled_file,
        "profile_vcf_path": filled_file,
        "family_ped_path": filled_file,
        "sv_vcf_path": None,
    }


@pytest.fixture(name="observations_input_files")
def fixture_observations_input_files(
    observations_input_files_raw: dict,
) -> MipDNAObservationsInputFiles:
    """Return raw observations input files for rare diseases WES analysis."""
    return MipDNAObservationsInputFiles(**observations_input_files_raw)


@pytest.fixture(name="balsamic_observations_input_files_raw")
def fixture_balsamic_observations_input_files_raw(case_id: str, filled_file: Path) -> dict:
    """Return raw observations input files for cancer."""
    return {
        "snv_vcf_path": filled_file,
        "snv_all_vcf_path": filled_file,
        "sv_vcf_path": filled_file,
        "profile_vcf_path": filled_file,
    }


@pytest.fixture(name="balsamic_observations_input_files")
def fixture_balsamic_observations_input_files(
    balsamic_observations_input_files_raw: dict,
) -> BalsamicObservationsInputFiles:
    """Return raw observations input files for cancer WGS analysis."""
    return BalsamicObservationsInputFiles(**balsamic_observations_input_files_raw)
