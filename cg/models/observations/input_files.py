"""Loqusdb input files models."""

import logging

from pydantic import BaseModel, FilePath

LOG = logging.getLogger(__name__)


class ObservationsInputFiles(BaseModel):
    """Model for validating Loqusdb input files."""

    snv_vcf_path: FilePath
    sv_vcf_path: FilePath | None = None


class MipDNAObservationsInputFiles(ObservationsInputFiles):
    """Model for validating rare disease Loqusdb input files."""

    profile_vcf_path: FilePath
    family_ped_path: FilePath


class BalsamicObservationsInputFiles(ObservationsInputFiles):
    """Model for validating cancer Loqusdb input files."""

    snv_germline_vcf_path: FilePath
    sv_germline_vcf_path: FilePath | None = None


class RarediseaseObservationsInputFiles(ObservationsInputFiles):
    """Model for validating RAREDISEASE Loqusdb input files."""

    profile_vcf_path: FilePath
    family_ped_path: FilePath
