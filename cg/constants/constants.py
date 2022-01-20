"""Constants for cg"""
from cgmodels.cg.constants import Pipeline, StrEnum

ANALYSIS_TYPES = ["tumor_wgs", "tumor_normal_wgs", "tumor_panel", "tumor_normal_panel"]

CAPTUREKIT_CANCER_OPTIONS = (
    "GIcfDNA",
    "GMCKsolid",
    "GMSmyeloid",
    "LymphoMATIC",
    "other (specify in comment field)",
)
CAPTUREKIT_OPTIONS = (
    "Agilent Sureselect CRE",
    "Agilent Sureselect V5",
    "SureSelect Focused Exome",
    "Twist_Target_hg19.bed",
    "other",
)

CASE_ACTIONS = ("analyze", "running", "hold")

COLLABORATORS = ("cust000", "cust002", "cust003", "cust004", "cust042")

COMBOS = {
    "DSD": ("DSD", "HYP", "SEXDIF", "SEXDET"),
    "CM": ("CNM", "CM"),
    "Horsel": ("Horsel", "141217", "141201"),
}

CONTAINER_OPTIONS = ("Tube", "96 well plate", "No container")

CONTROL_OPTIONS = ("", "negative", "positive")

DEFAULT_CAPTURE_KIT = "twistexomerefseq_9.1_hg19_design.bed"

FLOWCELL_STATUS = ("ondisk", "removed", "requested", "processing", "retrieved")

PREP_CATEGORIES = ("cov", "mic", "rml", "tgs", "wes", "wgs", "wts")

SARS_COV_REGEX = "^[0-9]{2}CS[0-9]{6}$"

SEX_OPTIONS = ("male", "female", "unknown")

STATUS_OPTIONS = ("affected", "unaffected", "unknown")


class DataDelivery(StrEnum):
    ANALYSIS_BAM_FILES: str = "analysis-bam"
    ANALYSIS_FILES: str = "analysis"
    FASTQ: str = "fastq"
    FASTQ_QC: str = "fastq_qc"
    FASTQ_QC_ANALYSIS_CRAM: str = "fastq_qc-analysis-cram"
    FASTQ_QC_ANALYSIS_CRAM_SCOUT: str = "fastq_qc-analysis-cram-scout"
    NIPT_VIEWER: str = "nipt-viewer"
    SCOUT: str = "scout"


class FlowCellStatus(StrEnum):
    ONDISK: str = "ondisk"
    REMOVED: str = "removed"
    REQUESTED: str = "requested"
    PROCESSING: str = "processing"
    RETRIEVED: str = "retrieved"


class HousekeeperTags(StrEnum):
    FASTQ: str = "fastq"
    SAMPLESHEET: str = "samplesheet"
    SPRING: str = "spring"
    ARCHIVED_SAMPLE_SHEET: str = "archived_sample_sheet"
