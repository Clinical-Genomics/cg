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
VALIDATION_CASES = [
    "bigdrum",
    "bosssponge",
    "brightcaiman",  # DNA rare disease positive control
    "busycolt",
    "casualgannet",  # DNA rare disease positive control
    "civilkoala",  # RNA rare disease positive control
    "cleanshrimp",  # DNA rare disease positive control
    "daringpony",
    "drivenmolly",  # RNA rare disease positive control
    "easybeetle",  # DNA rare disease positive control
    "epicasp",  # DNA rare disease positive control
    "expertmole",  # RNA rare disease positive control
    "finequagga",  # RNA rare disease positive control
    "firstfawn",  # DNA rare disease positive control
    "fleetjay",
    "frankhusky",
    "gamedeer",
    "gladthrush",  # DNA rare disease positive control
    "helpedfilly",  # DNA rare disease positive control
    "hotskink",  # DNA rare disease positive control
    "hotviper",
    "inferret",  # DNA rare disease positive control
    "intentcorgi",  # DNA rare disease positive control
    "intentmayfly",  # DNA rare disease positive control
    "justhusky",  # DNA rare disease positive control
    "keencalf",
    "keenviper",
    "kindcaiman",  # DNA rare disease positive control
    "lightprawn",  # DNA rare disease positive control
    "livingox",  # DNA rare disease positive control
    "luckyhog",
    "meetpossum",
    "newaphid",  # RNA rare disease positive control
    "nextjackal",  # DNA rare disease positive control
    "mintbaboon",
    "mintyeti",
    "modernmule",  # DNA rare disease positive control
    "moralcattle",  # RNA rare disease positive control
    "moralgoat",
    "onemite",  # DNA rare disease positive control
    "proeagle",
    "propercoral",
    "proudcougar",  # DNA rare disease positive control
    "pumpedcat",
    "rightmacaw",  # DNA rare disease positive control
    "safeguinea",  # DNA rare disease positive control
    "sharpparrot",  # RNA rare disease positive control
    "sharppigeon",  # DNA rare disease positive control
    "sharpwhale",  # DNA rare disease positive control
    "smoothboa",  # RNA rare disease positive control
    "strongbison",  # DNA rare disease positive control
    "strongman",
    "tenderoriole",  # DNA rare disease positive control
    "topsrhino",  # DNA rare disease positive control
    "unitedbeagle",
    "usablemarten",  # DNA rare disease positive control
    "vitalmouse",  # DNA rare disease positive control
]

CASES_TO_IGNORE = PROBLEMATIC_CASES + VALIDATION_CASES
