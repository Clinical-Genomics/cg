"""Constants for cg"""
from enum import Enum

from cg.utils.StrEnum import StrEnum

CONTAINER_OPTIONS = ("Tube", "96 well plate")

CAPTUREKIT_OPTIONS = (
    "Agilent Sureselect CRE",
    "Agilent Sureselect V5",
    "SureSelect Focused Exome",
    "Twist_Target_hg19.bed",
    "other",
)

CAPTUREKIT_CANCER_OPTIONS = (
    "GIcfDNA",
    "GMCKsolid",
    "GMSmyeloid",
    "LymphoMATIC",
    "other (specify in comment field)",
)

COMBOS = {
    "DSD": ("DSD", "HYP", "SEXDIF", "SEXDET"),
    "CM": ("CNM", "CM"),
    "Horsel": ("Horsel", "141217", "141201"),
}
COLLABORATORS = ("cust000", "cust002", "cust003", "cust004", "cust042")

DEFAULT_CAPTURE_KIT = "twistexomerefseq_9.1_hg19_design.bed"

CASE_ACTIONS = ("analyze", "running", "hold")

FLOWCELL_STATUS = ("ondisk", "removed", "requested", "processing")


class Pipeline(StrEnum):
    BALSAMIC: str = "balsamic"
    FASTQ: str = "fastq"
    FLUFFY: str = "fluffy"
    MICROSALT: str = "microsalt"
    MIP_DNA: str = "mip-dna"
    MIP_RNA: str = "mip-rna"


class DataDelivery(StrEnum):
    ANALYSIS_FILES: str = "analysis"
    ANALYSIS_BAM_FILES: str = "analysis-bam"
    FASTQ: str = "fastq"
    NIPT_VIEWER: str = "nipt-viewer"
    FASTQ_QC: str = "fastq_qc"
    SCOUT: str = "scout"


PREP_CATEGORIES = ("wgs", "wes", "tgs", "wts", "mic", "rml")

SEX_OPTIONS = ("male", "female", "unknown")

STATUS_OPTIONS = ("affected", "unaffected", "unknown")
ANALYSIS_TYPES = ["tumor_wgs", "tumor_normal_wgs", "tumor_panel", "tumor_normal_panel"]
