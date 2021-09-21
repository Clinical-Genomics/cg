"""Constants specific for compression"""
import datetime

# Constants for crunchy
FASTQ_FIRST_READ_SUFFIX = "_R1_001.fastq.gz"
FASTQ_SECOND_READ_SUFFIX = "_R2_001.fastq.gz"
SPRING_SUFFIX = ".spring"

# Number of days until fastqs counts as old
FASTQ_DELTA = 21
# Get the fastq delta in datetime format
FASTQ_DATETIME_DELTA = datetime.timedelta(days=FASTQ_DELTA)

PROBLEMATIC_CASES = [
    "causalmite",
    "deepcub",
    "expertalien",
    "fluenteagle",
    "grandkoi",
    "lovingmayfly",
    "loyalegret",
    "modernbee",
    "proudcollie",
    "richalien",
    "suremako",
    "wisestork",
]

# List of cases used for validation that we should skip
BALSAMIC_VALIDATION_CASES = [
    "bosssponge",  # BALSAMIC validation case tumor-only panel
    "civilsole",  # BALSAMIC validation case tumor-only wgs
    "fleetjay",  # BALSAMIC validation case tumor-normal wgs
    "moralgoat",  # BALSAMIC validation case tumor-normal wgs
    "sweetelf",  # BALSAMIC positive control tumor-only panel
    "unitedbeagle",  # BALSAMIC validation case tumor-normal panel
    "equalbug",  # UMI seracare validation case (AF 0.5%) tumor-normal panel
    "stableraven",  # UMI seracare validation case (AF 1%) tumor-normal panel
    "sunnyiguana",  # UMI seracare validation case (AF 0.1%) tumor-normal panel
    "uphippo",  # UMI seracare validation case (AF 0.5%) tumor-only panel
]

MIP_VALIDATION_CASES = [
    "brightcaiman",  # DNA rare disease positive control
    "casualgannet",  # DNA rare disease positive control
    "civilkoala",  # RNA rare disease positive control
    "cleanshrimp",  # DNA rare disease positive control
    "drivenmolly",  # RNA rare disease positive control
    "easybeetle",  # DNA rare disease positive control
    "epicasp",  # DNA rare disease positive control
    "expertmole",  # RNA rare disease positive control
    "finequagga",  # RNA rare disease positive control
    "firstfawn",  # DNA rare disease positive control
    "gladthrush",  # DNA rare disease positive control
    "helpedfilly",  # DNA rare disease positive control
    "hotskink",  # DNA rare disease positive control
    "inferret",  # DNA rare disease positive control
    "intentcorgi",  # DNA rare disease positive control
    "intentmayfly",  # DNA rare disease positive control
    "justhusky",  # DNA rare disease positive control
    "kindcaiman",  # DNA rare disease positive control
    "lightprawn",  # DNA rare disease positive control
    "livingox",  # DNA rare disease positive control
    "newaphid",  # RNA rare disease positive control
    "nextjackal",  # DNA rare disease positive control
    "modernmule",  # DNA rare disease positive control
    "moralcattle",  # RNA rare disease positive control
    "onemite",  # DNA rare disease positive control
    "opencow",  # DNA rare disease positive control
    "proudcougar",  # DNA rare disease positive control
    "rightmacaw",  # DNA rare disease positive control
    "safeguinea",  # DNA rare disease positive control
    "sharpparrot",  # RNA rare disease positive control
    "sharppigeon",  # DNA rare disease positive control
    "sharpwhale",  # DNA rare disease positive control
    "stillant",  # DNA rare disease positive control
    "smoothboa",  # RNA rare disease positive control
    "strongbison",  # DNA rare disease positive control
    "tenderoriole",  # DNA rare disease positive control
    "topsrhino",  # DNA rare disease positive control
    "usablemarten",  # DNA rare disease positive control
    "vitalmouse",  # DNA rare disease positive control
]

OTHER_VALIDATION_CASES = [
    "bigdrum",
    "busycolt",
    "daringpony",
    "frankhusky",
    "gamedeer",
    "hotviper",
    "keencalf",
    "keenviper",
    "luckyhog",
    "meetpossum",
    "mintbaboon",
    "mintyeti",
    "proeagle",
    "propercoral",
    "pumpedcat",
    "strongman",
]

CASES_TO_IGNORE = (
    PROBLEMATIC_CASES + OTHER_VALIDATION_CASES + BALSAMIC_VALIDATION_CASES + MIP_VALIDATION_CASES
)
