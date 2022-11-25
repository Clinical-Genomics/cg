"""Loqusdb related constants."""

from enum import Enum

from cgmodels.cg.constants import Pipeline, StrEnum

from cg.constants.sequencing import SequencingMethod

LOQUSDB_ID = "_id"
LOQUSDB_SUPPORTED_PIPELINES = [Pipeline.MIP_DNA, Pipeline.BALSAMIC]
LOQUSDB_MIP_SEQUENCING_METHODS = [SequencingMethod.WGS, SequencingMethod.WES]
LOQUSDB_BALSAMIC_SEQUENCING_METHODS = [SequencingMethod.WGS]


class LoqusdbInstance(StrEnum):
    """Observations instances."""

    WGS: str = "loqusdb"
    WES: str = "loqusdb-wes"
    SOMATIC: str = "loqusdb-somatic"
    TUMOR: str = "loqusdb-tumor"


class MipDNAObservationsAnalysisTag(StrEnum):
    """Rare disease observations files analysis tags."""

    SNV_VCF: str = "deepvariant"
    SV_VCF: str = "vcf-sv-research"
    PROFILE_GBCF: str = "snv-gbcf"
    FAMILY_PED: str = "pedigree"


class MipDNALoadParameters(Enum):
    """Rare disease Loqusdb load command parameters."""

    PROFILE_THRESHOLD: float = 0.95
    GQ_THRESHOLD: int = 10
    HARD_THRESHOLD: float = 0.95
    SOFT_THRESHOLD: float = 0.90


class BalsamicObservationsAnalysisTag(StrEnum):
    """Cancer observations files analysis tags."""

    SNV_VCF: str = "vcf-snv-clinical"
    SNV_ALL_VCF: str = "vcf-snv-germline-tumor"
    SV_VCF: str = "vcf-sv-clinical"
    PROFILE_VCF: str = "vcf-snv-germline-tumor"


class BalsamicLoadParameters(Enum):
    """Cancer Loqusdb load command parameters."""

    PROFILE_THRESHOLD: float = 0.95
    GQ_THRESHOLD: int = 10
    HARD_THRESHOLD: float = 0.95
    SOFT_THRESHOLD: float = 0.90
