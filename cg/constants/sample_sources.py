"""Constants that specify sample sources."""

from enum import StrEnum

METAGENOME_SOURCES = (
    "blood",
    "skin",
    "respiratory",
    "urine",
    "CSF",
    "faeces",
    "environmental",
    "unknown",
    "other",
)

ANALYSIS_SOURCES = (
    "blood",
    "buccal swab",
    "cell-free DNA",
    "cell line",
    "cytology (FFPE)",
    "cytology (not fixed/fresh)",
    "cytology (fixed)",
    "fibroblast",
    "muscle",
    "nail",
    "saliva",
    "skin",
    "tissue (FFPE)",
    "tissue (fresh frozen)",
    "bone marrow",
    "other",
)


class SourceType(StrEnum):
    BLOOD: str = "blood"
    BONE_MARROW: str = "bone marrow"
    BUCCAL_SWAB: str = "buccal swab"
    CELL_FREE_DNA: str = "cell-free DNA"
    CELL_LINE: str = "cell line"
    CYTOLOGY: str = "cytology (not fixed/fresh)"
    CYTOLOGY_FFPE: str = "cytology (FFPE)"
    FFPE: str = "FFPE"
    FIBROBLAST: str = "fibroblast"
    MUSCLE: str = "muscle"
    NAIL: str = "nail"
    OTHER: str = "other"
    SALIVA: str = "saliva"
    SKIN: str = "skin"
    TISSUE: str = "tissue (fresh frozen)"
    TISSUE_FFPE: str = "tissue (FFPE)"
    UNKNOWN: str = "unknown"
