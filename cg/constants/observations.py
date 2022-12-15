"""Loqusdb related constants."""

from enum import Enum

from cgmodels.cg.constants import Pipeline, StrEnum

from cg.constants.sequencing import SequencingMethod

LOQUSDB_ID = "_id"
LOQUSDB_SUPPORTED_PIPELINES = [Pipeline.MIP_DNA, Pipeline.BALSAMIC]
LOQUSDB_MIP_SEQUENCING_METHODS = [SequencingMethod.WGS, SequencingMethod.WES]
LOQUSDB_BALSAMIC_SEQUENCING_METHODS = [SequencingMethod.WGS]


class LoqusdbMipCustomers(StrEnum):
    """Loqusdb Rare Disease customers."""

    KLINISK_GENETIK: str = "cust002"
    CMMS: str = "cust003"
    KLINISK_IMMUNOLOGI: str = "cust004"


class LoqusdbBalsamicCustomers(StrEnum):
    """Loqusdb Balsamic customers."""

    AML: str = "cust110"
    BTB_GMS: str = "cust127"
    ONKPAT_HAGLUND: str = "cust143"
    BTB_GMS_LINKOPING: str = "cust147"


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
    CANCER_ALL_SNV: str = "cancer_all_snv"
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

    SNV_VCF: str = "vcf-snv"
    SNV_ALL_VCF: str = "vcf-snv-germline-tumor"
    SV_VCF: str = "vcf-sv"
    PROFILE_VCF: str = "vcf-snv-germline-tumor"


class BalsamicLoadParameters(Enum):
    """Cancer Loqusdb load command parameters."""

    PROFILE_THRESHOLD: float = 0.95
    GQ_THRESHOLD: int = 10
    HARD_THRESHOLD: float = 0.95
    SOFT_THRESHOLD: float = 0.90
