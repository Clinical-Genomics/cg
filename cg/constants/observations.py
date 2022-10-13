"""Loqusdb related constants."""

from enum import Enum

from cgmodels.cg.constants import Pipeline, StrEnum


LOQUSDB_SUPPORTED_PIPELINES = [Pipeline.MIP_DNA, Pipeline.BALSAMIC]


class MipDNAObservationsAnalysisTag(StrEnum):
    """Observations files analysis tags."""

    SNV_VCF: str = "deepvariant"
    SV_VCF: str = "vcf-sv-research"
    PROFILE_GBCF: str = "snv-gbcf"
    FAMILY_PED: str = "pedigree"


class MipDNALoadParameters(Enum):
    """MipDNA Loqusdb load command parameters."""

    PROFILE_THRESHOLD: float = 0.95
    GQ_THRESHOLD: int = 10
    HARD_THRESHOLD: float = 0.95
    SOFT_THRESHOLD: float = 0.90
