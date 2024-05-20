"""Loqusdb related constants."""

from enum import Enum, StrEnum

from cg.constants.constants import CancerAnalysisType, CustomerId, Workflow
from cg.constants.sequencing import SequencingMethod

LOQUSDB_ID = "_id"
LOQUSDB_SUPPORTED_WORKFLOWS = [Workflow.MIP_DNA, Workflow.BALSAMIC]
LOQUSDB_RARE_DISEASE_CUSTOMERS = [CustomerId.CUST002, CustomerId.CUST003, CustomerId.CUST004]
LOQUSDB_CANCER_CUSTOMERS = [
    CustomerId.CUST110,
    CustomerId.CUST127,
    CustomerId.CUST143,
    CustomerId.CUST147,
]
LOQUSDB_RARE_DISEASE_SEQUENCING_METHODS = [SequencingMethod.WGS, SequencingMethod.WES]
LOQUSDB_CANCER_SEQUENCING_METHODS = [
    CancerAnalysisType.TUMOR_WGS,
    CancerAnalysisType.TUMOR_NORMAL_WGS,
]


class LoqusdbInstance(StrEnum):
    """Observations instances."""

    WGS: str = "loqusdb"
    WES: str = "loqusdb-wes"
    SOMATIC: str = "loqusdb-somatic"
    TUMOR: str = "loqusdb-tumor"


class ObservationsFileWildcards(StrEnum):
    """File patterns regarding dump Loqusdb files."""

    CLINICAL_SNV: str = "clinical_snv"
    CLINICAL_SV: str = "clinical_sv"
    CANCER_GERMLINE_SNV: str = "cancer_germline_snv"
    CANCER_GERMLINE_SV: str = "cancer_germline_sv"
    CANCER_SOMATIC_SNV: str = "cancer_somatic_snv"
    CANCER_SOMATIC_SV: str = "cancer_somatic_sv"


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

    SNV_GERMLINE_VCF: str = "vcf-snv-germline-tumor"
    SNV_VCF: str = "vcf-snv-clinical"
    SV_GERMLINE_VCF: str = "vcf-sv-germline-tumor"
    SV_VCF: str = "vcf-sv-clinical"


class BalsamicLoadParameters(Enum):
    """Cancer Loqusdb load command parameters."""

    QUAL_THRESHOLD: int = 0
    QUAL_GERMLINE_THRESHOLD: int = 10
