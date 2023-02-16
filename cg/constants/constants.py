"""Constants for cg."""
import click
from cgmodels.cg.constants import StrEnum

from cg.constants.sequencing import Sequencers
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
    HOLD: str = "hold"
    RUNNING: str = "running"


CASE_ACTIONS = [action.value for action in CaseActions]

COLLABORATORS = ("cust000", "cust002", "cust003", "cust004", "cust042")

COMBOS = {
    "DSD": ("DSD", "HYP", "SEXDIF", "SEXDET"),
    "CM": ("CNM", "CM"),
    "Horsel": ("Horsel", "141217", "141201"),
}

CONTAINER_OPTIONS = ("Tube", "96 well plate", "No container")

CONTROL_OPTIONS = ("", "negative", "positive")

DEFAULT_CAPTURE_KIT = "twistexomerefseq_9.1_hg19_design.bed"


class FlowCellStatus(StrEnum):
    ONDISK: str = "ondisk"
    REMOVED: str = "removed"
    REQUESTED: str = "requested"
    PROCESSING: str = "processing"
    RETRIEVED: str = "retrieved"


FLOWCELL_STATUS = [status.value for status in FlowCellStatus]

FLOWCELL_Q30_THRESHOLD = {
    Sequencers.HISEQX: 75,
    Sequencers.HISEQGA: 80,
    Sequencers.NOVASEQ: 75,
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


class SampleType(StrEnum):
    TUMOR: str = "tumor"
    NORMAL: str = "normal"


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


class HastaSlurmPartitions(StrEnum):
    DRAGEN: str = "dragen"


class FileExtensions(StrEnum):
    GPG: str = ".gpg"
    GZIP: str = ".gz"
    JSON: str = ".json"
    KEY: str = ".key"
    NO_EXTENSION: str = ""
    SPRING: str = ".spring"
    TAR: str = ".tar"
    TMP: str = ".tmp"
    VCF: str = ".vcf"


class APIMethods(StrEnum):
    POST: str = "POST"
    PUT: str = "PUT"
    GET: str = "GET"
    DELETE: str = "DELETE"
    PATCH: str = "PATCH"


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


class MicrosaltQC:
    QC_PERCENT_THRESHOLD_MWX: float = 0.1
    COVERAGE_10X_THRESHOLD: float = 0.75
    NEGATIVE_CONTROL_READS_THRESHOLD: float = 0.2
    TARGET_READS: int = 6000000


class MicrosaltAppTags(StrEnum):
    MWRNXTR003: str = "MWRNXTR003"
    MWXNXTR003: str = "MWXNXTR003"
    APP_TYPE: str = "mic"


DRY_RUN_MESSAGE = "Dry run: process call will not be executed!"
