"""Loqusdb related constants."""

from cgmodels.cg.constants import Pipeline, StrEnum


LOQUSDB_SUPPORTED_PIPELINES = [Pipeline.MIP_DNA, Pipeline.BALSAMIC]


class MipDNAObservationsAnalysisTag(StrEnum):
    PEDIGREE: str = "pedigree"
    CHECK_PROFILE_GBCF: str = "snv-gbcf"
    SNV_VARIANTS: str = "deepvariant"
    SV_VARIANTS: str = "vcf-sv-research"
