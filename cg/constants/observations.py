"""Loqusdb related constants."""

from enum import Enum, StrEnum

from cg.constants.constants import CancerAnalysisType, CustomerId, Workflow
from cg.constants.sequencing import SeqLibraryPrepCategory

LOQUSDB_ID = "_id"
LOQUSDB_SUPPORTED_WORKFLOWS = [
    Workflow.BALSAMIC,
    Workflow.MIP_DNA,
    Workflow.NALLO,
    Workflow.RAREDISEASE,
]
LOQUSDB_RARE_DISEASE_CUSTOMERS = [CustomerId.CUST002, CustomerId.CUST003, CustomerId.CUST004]
LOQUSDB_CANCER_CUSTOMERS = [
    CustomerId.CUST002,
    CustomerId.CUST087,
    CustomerId.CUST110,
    CustomerId.CUST127,
    CustomerId.CUST143,
    CustomerId.CUST147,
    CustomerId.CUST175,
    CustomerId.CUST185,
]
LOQUSDB_LONG_READ_CUSTOMERS = [
    CustomerId.CUST002,
    CustomerId.CUST003,
    CustomerId.CUST004,
    CustomerId.CUST201,
]
LOQUSDB_LONG_READ_SEQUENCING_METHODS = [
    SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING,
]
LOQUSDB_RARE_DISEASE_SEQUENCING_METHODS = [
    SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING,
    SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING,
]
LOQUSDB_CANCER_SEQUENCING_METHODS = [
    CancerAnalysisType.TUMOR_WGS,
    CancerAnalysisType.TUMOR_NORMAL_WGS,
    CancerAnalysisType.TUMOR_PANEL,
]


class BalsamicObservationPanel(StrEnum):
    """Group of panels which have associated LoqusDB instances."""

    EXOME = "Twist Exome Comprehensive"
    LYMPHOID = "GMSlymphoid"
    MYELOID = "GMSmyeloid"


class BalsamicLoadParameters(Enum):
    """Cancer Loqusdb load command parameters."""

    QUAL_THRESHOLD: int = 0
    QUAL_GERMLINE_THRESHOLD: int = 10


class BalsamicObservationsAnalysisTag(StrEnum):
    """Cancer observations files analysis tags."""

    SNV_GERMLINE_VCF: str = "vcf-snv-germline-tumor"
    SNV_VCF: str = "vcf-snv-clinical"
    SV_GERMLINE_VCF: str = "vcf-sv-germline-tumor"
    SV_VCF: str = "vcf-sv-clinical"


class LoqusdbInstance(StrEnum):
    """Observations instances."""

    LWP = "loqusdb-lwp"
    WGS = "loqusdb"
    WES = "loqusdb-wes"
    SOMATIC = "loqusdb-somatic"
    TUMOR = "loqusdb-tumor"
    SOMATIC_LYMPHOID = "loqusdb-somatic-lymphoid"
    SOMATIC_MYELOID = "loqusdb-somatic-myeloid"
    SOMATIC_EXOME = "loqusdb-somatic-exome"


class MipDNALoadParameters(Enum):
    """Rare disease Loqusdb load command parameters."""

    PROFILE_THRESHOLD: float = 0.95
    GQ_THRESHOLD: int = 10
    HARD_THRESHOLD: float = 0.95
    SOFT_THRESHOLD: float = 0.90


class MipDNAObservationsAnalysisTag(StrEnum):
    """Rare disease observations files analysis tags."""

    SNV_VCF: str = "deepvariant"
    SV_VCF: str = "vcf-sv-research"
    PROFILE_GBCF: str = "snv-gbcf"
    FAMILY_PED: str = "pedigree"


class NalloObservationsAnalysisTag(StrEnum):
    """Nallo observations files analysis tags."""

    SNV_VCF = "vcf-snv-research"
    SV_VCF = "vcf-sv-research"
    FAMILY_PED = "pedigree"


class NalloLoadParameters(Enum):
    """Nallo Loqusdb load command parameters."""

    PROFILE_THRESHOLD = 0.95
    GQ_THRESHOLD = 10
    HARD_THRESHOLD = 0.95
    SOFT_THRESHOLD = 0.90
    SNV_GQ_ONLY = True


class ObservationsFileWildcards(StrEnum):
    """File patterns regarding dump Loqusdb files."""

    ARTEFACT_SNV: str = "artefact_somatic_snv"
    CLINICAL_SNV: str = "clinical_snv"
    CLINICAL_SV: str = "clinical_sv"
    CANCER_GERMLINE_SNV: str = "cancer_germline_snv"
    CANCER_GERMLINE_SV: str = "cancer_germline_sv"
    CANCER_SOMATIC_SNV: str = "cancer_somatic_snv"
    CANCER_SOMATIC_SV: str = "cancer_somatic_sv"


class RarediseaseObservationsAnalysisTag(StrEnum):
    """Rare disease observations files analysis tags."""

    SNV_VCF: str = "vcf-snv"
    SV_VCF: str = "vcf-sv"
    FAMILY_PED: str = "pedigree"


class RarediseaseLoadParameters(Enum):
    """Raredisease Loqusdb load command parameters."""

    PROFILE_THRESHOLD: float = 0.95
    GQ_THRESHOLD: int = 10
    HARD_THRESHOLD: float = 0.95
    SOFT_THRESHOLD: float = 0.90
