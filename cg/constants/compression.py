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
    "busycolt",
    "casualgannet",
    "civilkoala",
    "cleanshrimp",
    "daringpony",
    "drivenmolly",
    "easybeetle",
    "epicasp",
    "expertmole",
    "finequagga",
    "firstfawn",
    "fleetjay",
    "frankhusky",
    "gamedeer",
    "gladthrush",
    "helpedfilly",
    "hotskink",
    "hotviper",
    "intentcorgi",
    "intentmayfly",
    "keencalf",
    "keenviper",
    "lightprawn",
    "livingox",
    "luckyhog",
    "meetpossum",
    "newaphid",
    "mintbaboon",
    "mintyeti",
    "moralcattle",
    "moralgoat",
    "onemite",
    "proeagle",
    "propercoral",
    "pumpedcat",
    "rightmacaw",
    "safeguinea",
    "sharpparrot",
    "sharppigeon",
    "smoothboa",
    "strongbison",
    "strongman",
    "topsrhino",
    "unitedbeagle",
    "usablemarten",
    "vitalmouse",
]

CASES_TO_IGNORE = PROBLEMATIC_CASES + VALIDATION_CASES
