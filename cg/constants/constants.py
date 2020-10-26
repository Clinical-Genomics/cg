"""Constans for cg"""

TMP_DIR = "/home/proj/production/rare-disease/temp-dir/"

PRIORITY_MAP = {"research": 0, "standard": 1, "priority": 2, "express": 3, "clinical trials": 4}
REV_PRIORITY_MAP = {value: key for key, value in PRIORITY_MAP.items()}
PRIORITY_OPTIONS = list(PRIORITY_MAP.keys())
FAMILY_ACTIONS = ("analyze", "running", "hold")
PREP_CATEGORIES = ("wgs", "wes", "tgs", "wts", "mic", "rml")
SEX_OPTIONS = ("male", "female", "unknown")
STATUS_OPTIONS = ("affected", "unaffected", "unknown")
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
DEFAULT_CAPTURE_KIT = "twistexomerefseq_9.1_hg19_design.bed"

COMBOS = {
    "DSD": ("DSD", "HYP", "SEXDIF", "SEXDET"),
    "CM": ("CNM", "CM"),
    "Horsel": ("Horsel", "141217", "141201"),
}
COLLABORATORS = ("cust000", "cust002", "cust003", "cust004", "cust042")
MASTER_LIST = (
    "BRAIN",
    "Cardiology",
    "CTD",
    "ENDO",
    "EP",
    "IBMFS",
    "IEM",
    "IF",
    "NEURODEG",
    "NMD",
    "mcarta",
    "MIT",
    "MOVE",
    "mtDNA",
    "PEDHEP",
    "PID",
    "PIDCAD",
    "OMIM-AUTO",
    "SKD",
)
FLOWCELL_STATUS = ("ondisk", "removed", "requested", "processing")
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
    "muscle",
    "nail",
    "saliva",
    "skin",
    "tissue (FFPE)",
    "tissue (fresh frozen)",
    "bone marrow",
    "other",
)
NO_PARENT = "0"

# Constants for crunchy
FASTQ_FIRST_READ_SUFFIX = "_R1_001.fastq.gz"
FASTQ_SECOND_READ_SUFFIX = "_R2_001.fastq.gz"
SPRING_SUFFIX = ".spring"
# Number of days until fastqs counts as old
FASTQ_DELTA = 21

# Symbols
SINGLE_QUOTE = "'"
SPACE = " "

# Processes
RETURN_SUCCESS = 0
EXIT_SUCCESS = 0
EXIT_FAIL = 1
