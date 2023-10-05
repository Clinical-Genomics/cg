"""ObservationsInputFiles test fixtures."""
from pathlib import Path

import pytest

from cg.models.observations.input_files import (
    BalsamicObservationsInputFiles,
    MipDNAObservationsInputFiles,
)


@pytest.fixture(name="observations_input_files_raw")
def observations_input_files_raw(case_id: str, filled_file: Path) -> dict:
    """Return raw observations input files for rare diseases."""
    return {
        "family_ped_path": filled_file,
        "profile_vcf_path": filled_file,
        "snv_vcf_path": filled_file,
        "sv_vcf_path": None,
    }


@pytest.fixture(name="observations_input_files")
def observations_input_files(
    observations_input_files_raw: dict,
) -> MipDNAObservationsInputFiles:
    """Return raw observations input files for rare diseases WES analysis."""
    return MipDNAObservationsInputFiles(**observations_input_files_raw)


@pytest.fixture(name="balsamic_observations_input_files_raw")
def balsamic_observations_input_files_raw(case_id: str, filled_file: Path) -> dict:
    """Return raw observations input files for cancer."""
    return {
        "snv_germline_vcf_path": filled_file,
        "snv_vcf_path": filled_file,
        "sv_germline_vcf_path": filled_file,
        "sv_vcf_path": filled_file,
    }


@pytest.fixture(name="balsamic_observations_input_files")
def balsamic_observations_input_files(
    balsamic_observations_input_files_raw: dict,
) -> BalsamicObservationsInputFiles:
    """Return raw observations input files for cancer WGS analysis."""
    return BalsamicObservationsInputFiles(**balsamic_observations_input_files_raw)
