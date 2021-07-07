from cgmodels.cg.constants import StrEnum


class ObservationAnalysisType(StrEnum):
    WGS: str = "wgs"


class ObservationAnalysisTag(StrEnum):
    PEDIGREE: str = "pedigree"
    CHECK_PROFILE_GBCF: str = "snv-gbcf"
    SNV_VARIANTS: str = "deepvariant"
    SV_VARIANTS: str = "vcf-sv-research"
