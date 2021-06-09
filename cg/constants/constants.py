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


class DataDelivery(StrEnum):
    ANALYSIS_FILES: str = "analysis"
    ANALYSIS_BAM_FILES: str = "analysis-bam"
    FASTQ: str = "fastq"
    NIPT_VIEWER: str = "nipt-viewer"
    FASTQ_QC: str = "fastq_qc"
    SCOUT: str = "scout"


class OrderType(StrEnum):
    BALSAMIC: str = str(Pipeline.BALSAMIC)
    EXTERNAL: str = "external"
    FASTQ: str = str(Pipeline.FASTQ)
    FLUFFY: str = str(Pipeline.FLUFFY)
    METAGENOME: str = "metagenome"
    MICROSALT: str = str(Pipeline.MICROSALT)
    MIP_DNA: str = str(Pipeline.MIP_DNA)
    MIP_RNA: str = str(Pipeline.MIP_RNA)
    RML: str = "rml"
    SARS_COV_2: str = str(Pipeline.SARS_COV_2)


COLLABORATORS = ("cust000", "cust002", "cust003", "cust004", "cust042")

COMBOS = {
    "DSD": ("DSD", "HYP", "SEXDIF", "SEXDET"),
    "CM": ("CNM", "CM"),
    "Horsel": ("Horsel", "141217", "141201"),
}
CONTAINER_OPTIONS = ("Tube", "96 well plate")

DEFAULT_CAPTURE_KIT = "twistexomerefseq_9.1_hg19_design.bed"

FLOWCELL_STATUS = ("ondisk", "removed", "requested", "processing", "retrieved")

PREP_CATEGORIES = ("cov", "mic", "rml", "tgs", "wes", "wgs", "wts")

SEX_OPTIONS = ("male", "female", "unknown")

STATUS_OPTIONS = ("affected", "unaffected", "unknown")
