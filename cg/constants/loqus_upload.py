from cgmodels.cg.constants import StrEnum


class ObservationAnalysisType(StrEnum):
    WGS: str = "wgs"


class ObservationAnalysisTag(StrEnum):
    PEDIGREE: str = "pedigree"
    CHECK_PROFILE_GBCF: str = "snv-gbcf"
    SNV_VARIANTS: str = "deepvariant"
    SV_VARIANTS: str = "vcf-sv-research"


class ObservationFileWildcards(StrEnum):
    """Cancer file patterns regarding dump loqusdb files."""

    CLINICAL_SNV: str = "clinical_snv"
    CLINICAL_SV: str = "clinical_sv"
    CANCER_ALL_SNV: str = "cancer_all_snv"
    CANCER_SOMATIC_SNV: str = "cancer_somatic_snv"
    CANCER_SOMATIC_SV: str = "cancer_somatic_sv"
