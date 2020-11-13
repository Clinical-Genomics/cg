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

FAMILY_ACTIONS = ("analyze", "running", "hold")

FLOWCELL_STATUS = ("ondisk", "removed", "requested", "processing")


class Pipeline(StrEnum):
    BALSAMIC: str = "balsamic"
    FASTQ: str = "fastq"
    MICROSALT: str = "microsalt"
    MIP_DNA: str = "mip-dna"
    MIP_RNA: str = "mip-rna"


class DataDelivery(StrEnum):
    FASTQ: str = "fastq"
    QC: str = "custom"


PREP_CATEGORIES = ("wgs", "wes", "tgs", "wts", "mic", "rml")

SEX_OPTIONS = ("male", "female", "unknown")

STATUS_OPTIONS = ("affected", "unaffected", "unknown")
