"""ObservationsInputFiles test fixtures."""

from pathlib import Path

import pytest

from cg.models.observations.input_files import MipDNAObservationsInputFiles


@pytest.fixture(name="observations_input_files_dict")
def fixture_observations_input_files_dict(case_id: str, filled_file: Path) -> dict:
    """Raw observations input files for rare diseases."""
    return {
        "snv_vcf_path": filled_file,
        "profile_vcf_path": filled_file,
        "family_ped_path": filled_file,
        "sv_vcf_path": None,
    }


@pytest.fixture(name="observations_input_files")
def fixture_observations_input_files(
    observations_input_files_dict: dict,
) -> MipDNAObservationsInputFiles:
    """Observations input file model for rare diseases."""
    return MipDNAObservationsInputFiles(**observations_input_files_dict)
