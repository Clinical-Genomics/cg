"""Constants for cg"""
import click
from cgmodels.cg.constants import Pipeline, StrEnum

from cg.utils.date import get_date


VALID_DATA_IN_PRODUCTION = get_date("2017-09-27")

MAX_ITEMS_TO_RETRIEVE = 50

SCALE_TO_MILLION_READ_PAIRS = 2_000_000

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


class CaseActions(StrEnum):
    ANALYZE: str = "analyze"


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

FLOWCELL_Q30_THRESHOLD = {
    "hiseqx": 75,
    "hiseqga": 80,
    "novaseq": 75,
}


class PrepCategory(StrEnum):
    COVID: str = "cov"
    MICROBIAL: str = "mic"
    READY_MADE_LIBRARY: str = "rml"
    TARGETED_GENOME_SEQUENCING: str = "tgs"
    WHOLE_EXOME_SEQUENCING: str = "wes"
    WHOLE_GENOME_SEQUENCING: str = "wgs"
    WHOLE_TRANSCRIPTOME_SEQUENCING: str = "wts"


PREP_CATEGORIES = ("cov", "mic", "rml", "tgs", "wes", "wgs", "wts")

SEX_OPTIONS = ("male", "female", "unknown")

SARS_COV_REGEX = "^[0-9]{2}CS[0-9]{6}$"

STATUS_OPTIONS = ("affected", "unaffected", "unknown")


class FileFormat(StrEnum):
    JSON: str = "json"
    YAML: str = "yaml"


class GenomeVersion(StrEnum):
    hg19: str = "hg19"
    hg38: str = "hg38"
    canfam3: str = "canfam3"


class DataDelivery(StrEnum):
    ANALYSIS_FILES: str = "analysis"
    ANALYSIS_SCOUT: str = "analysis-scout"
    FASTQ: str = "fastq"
    FASTQ_SCOUT: str = "fastq-scout"
    FASTQ_QC: str = "fastq_qc"
    FASTQ_ANALYSIS: str = "fastq-analysis"
    FASTQ_QC_ANALYSIS: str = "fastq_qc-analysis"
    FASTQ_ANALYSIS_SCOUT: str = "fastq-analysis-scout"
    NIPT_VIEWER: str = "nipt-viewer"
    NO_DELIVERY: str = "no-delivery"
    SCOUT: str = "scout"
    STATINA: str = "statina"


class FlowCellStatus(StrEnum):
    ONDISK: str = "ondisk"
    REMOVED: str = "removed"
    REQUESTED: str = "requested"
    PROCESSING: str = "processing"
    RETRIEVED: str = "retrieved"


class HastaSlurmPartitions(StrEnum):
    DRAGEN: str = "dragen"


class HousekeeperTags(StrEnum):
    FASTQ: str = "fastq"
    SAMPLESHEET: str = "samplesheet"
    SPRING: str = "spring"
    ARCHIVED_SAMPLE_SHEET: str = "archived_sample_sheet"


class Sequencers(StrEnum):
    HISEQX: str = "hiseqx"
    HISEQGA: str = "hiseqga"
    NOVASEQ: str = "novaseq"
    ALL: str = "all"


class FileExtensions(StrEnum):
    GPG: str = ".gpg"
    GZIP: str = ".gz"
    JSON: str = ".json"
    KEY: str = ".key"
    NO_EXTENSION: str = ""
    SPRING: str = ".spring"
    TAR: str = ".tar"
    TMP: str = ".tmp"


DRY_RUN = click.option(
    "-d",
    "--dry-run",
    is_flag=True,
    default=False,
    help="Runs the command without making any changes",
)

SKIP_CONFIRMATION = click.option(
    "-y",
    "--yes",
    is_flag=True,
    default=False,
    help="Skip confirmation",
)
