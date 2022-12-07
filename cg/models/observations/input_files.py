"""Loqusdb input files models."""

import logging
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, validator


LOG = logging.getLogger(__name__)


def validate_observations_file(file: Path) -> Path:
    """Check if file exists in file system."""
    if file and not file.exists():
        LOG.error(f"File {file} could not be found")
        raise FileNotFoundError
    return file


class ObservationsInputFiles(BaseModel):
    """Model for validating Loqusdb input files."""

    snv_vcf_path: Path
    sv_vcf_path: Optional[Path] = None

    _ = validator("snv_vcf_path", "sv_vcf_path", always=False, allow_reuse=True)(
        validate_observations_file
    )


class MipDNAObservationsInputFiles(ObservationsInputFiles):
    """Model for validating rare disease Loqusdb input files."""

    profile_vcf_path: Path
    family_ped_path: Path

    _ = validator("family_ped_path", "profile_vcf_path", always=False, allow_reuse=True)(
        validate_observations_file
    )


class BalsamicObservationsInputFiles(ObservationsInputFiles):
    """Model for validating cancer Loqusdb input files."""

    snv_all_vcf_path: Path

    _ = validator("snv_all_vcf_path", always=False, allow_reuse=True)(validate_observations_file)
