"""Loqusdb input files fixtures."""

from pathlib import Path

import pytest

from cg.models.observations.input_files import (
    BalsamicObservationsInputFiles,
    MipDNAObservationsInputFiles,
    RarediseaseObservationsInputFiles,
)


@pytest.fixture
def balsamic_observations_input_files_raw(case_id: str, filled_file: Path) -> dict[str, Path]:
    """Return raw observations input files for cancer."""
    return {
        "snv_germline_vcf_path": filled_file,
        "snv_vcf_path": filled_file,
        "sv_germline_vcf_path": filled_file,
        "sv_vcf_path": filled_file,
    }


@pytest.fixture
def balsamic_observations_input_files(
    balsamic_observations_input_files_raw: dict[str, Path],
) -> BalsamicObservationsInputFiles:
    """Return raw observations input files for cancer WGS analysis."""
    return BalsamicObservationsInputFiles(**balsamic_observations_input_files_raw)


@pytest.fixture
def mip_dna_observations_input_files_raw(case_id: str, filled_file: Path) -> dict[str, Path]:
    """Return raw observations input files for rare diseases."""
    return {
        "family_ped_path": filled_file,
        "profile_vcf_path": filled_file,
        "snv_vcf_path": filled_file,
        "sv_vcf_path": None,
    }


@pytest.fixture
def mip_dna_observations_input_files(
    mip_dna_observations_input_files_raw: dict[str, Path],
) -> MipDNAObservationsInputFiles:
    """Return raw observations input files for rare diseases WES analysis."""
    return MipDNAObservationsInputFiles(**mip_dna_observations_input_files_raw)


@pytest.fixture
def raredisease_observations_input_files_raw(
    case_id: str, filled_file: Path
) -> dict[str, Path | None]:
    """Return raw observations input files for RAREDISEASE."""
    return {
        "family_ped_path": filled_file,
        "profile_vcf_path": filled_file,
        "snv_vcf_path": filled_file,
        "sv_vcf_path": None,
    }


@pytest.fixture
def raredisease_observations_input_files(
    raredisease_observations_input_files_raw: dict[str, Path],
) -> RarediseaseObservationsInputFiles:
    """Return raw observations input files for RAREDISEASE WES analysis."""
    return RarediseaseObservationsInputFiles(**raredisease_observations_input_files_raw)
