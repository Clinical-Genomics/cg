"""Constants specific for compression."""
import datetime
from typing import List

# Constants for crunchy
FASTQ_FIRST_READ_SUFFIX: str = "_R1_001.fastq.gz"
FASTQ_SECOND_READ_SUFFIX: str = "_R2_001.fastq.gz"
FLAG_PATH_SUFFIX: str = ".crunchy.txt"
MAX_READS_PER_GB: int = 18_000_000
CRUNCHY_MIN_GB_PER_PROCESS: int = 30
PENDING_PATH_SUFFIX: str = ".crunchy.pending.txt"


# Number of days until FASTQs counts as old
FASTQ_DELTA = 21
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
    "setamoeba",  # BALSAMIC validation case tumor-only panel
    "sweetelf",  # BALSAMIC positive control tumor-only panel
    "poeticghoul",  # BALSAMIC positive control tumor-only panel
    "equalbug",  # UMI seracare validation case (AF 0.5%) tumor-normal panel
    "stableraven",  # UMI seracare validation case (AF 1%) tumor-normal panel
    "uphippo",  # UMI seracare validation case (AF 0.5%) tumor-only panel
    "cleanfowl",  # BALSAMIC validation case, HD829 reference for FLT3 Ascertation
    "proudsquid",  # BALSAMIC validation case, HD829 reference for FLT3 Ascertation
    "modestjaguar",  # BALSAMIC validation case, HD829 reference for FLT3 Ascertation
    "dearmarmot",  # BALSAMIC validation case, HD829 reference for FLT3 Ascertation
    "holykid",  # BALSAMIC validation case, HD829 reference for FLT3 Ascertation
    "civilsole",  # BALSAMIC validation case tumor-only wgs
    "fleetjay",  # BALSAMIC validation case tumor-normal wgs
    "grandmarmot",  # BALSAMIC validation case tumor-normal wgs
    "unitedbeagle",  # BALSAMIC validation case tumor-normal panel
    "rightthrush",  # BALSAMIC validation case tumor-only wes
    "properpigeon",  # BALSAMIC validation case tumor-normal wes
    "eagerox",  # BALSAMIC validation case from cust087, tumor-only panel
    "casualweasel",  # BALSAMIC validation case from cust087, tumor-only panel
    "acetuna",  # BALSAMIC validation case from cust087, tumor-only panel
    "suitedsnake",  # BALSAMIC validation case from cust087, tumor-only panel
    "savinghorse",  # BALSAMIC validation case from cust087, tumor-only panel
    "rightpup",  # BALSAMIC validation case from cust087, tumor-only panel
    "sureroughy",  # BALSAMIC validation case from cust087, tumor-only panel
    "notedshark",  # BALSAMIC validation case from cust127, tumor-normal WGS (SV inversion positive control)
    "wholewhale",  # BALSAMIC validation case from cust143, tumor-normal WGS (SV translocation positive control)
    "largeturtle",  # BALSAMIC validation case from cust143, tumor-normal WGS (SV translocation positive control)
    "lightkodiak",  # BALSAMIC validation case from cust143, tumor-normal WGS (SV inversion positive control)
    "wholecivet",  # BALSAMIC validation case from cust110, tumor-normal WGS (SV inversion positive control)
    "upwardstork",  # BALSAMIC validation case from cust110, tumor-normal WGS (SV deletion positive control)
    "suitedgrub",  # BALSAMIC validation case from cust110, tumor-normal WGS (SV deletion positive control)
]

FLUFFY_VALIDATION_CASES = [
    "simplesalmon",  # Chromosome 13, 18, 21 Suspected
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

# List of cases used for validation that we should skip
RNAFUSION_VALIDATION_CASES = [
    "cuddlyhen",  # downsampled seracare commercial sample
    "oncrab",
    "daringowl",
    "growndoe",
    "stablemoray",
    "truemole",
    "rightmoray",
    "handyturtle",
    "inlab",
    "honestswine",
    "holyrodent",
    "expertboar",
    "bossmink",
    "ampleray",
    "nearbyjoey",
]

TAXPROFILER_VALIDATION_CASES: List[str] = [
    "richurchin",
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
    "maturejay",  # sars-cov-2 case
    "meetpossum",
    "mintbaboon",
    "mintyeti",
    "proeagle",
    "propercoral",
    "pumpedcat",
    "strongman",
    "truecoyote",
]

CASES_TO_IGNORE = (
    PROBLEMATIC_CASES
    + OTHER_VALIDATION_CASES
    + BALSAMIC_VALIDATION_CASES
    + FLUFFY_VALIDATION_CASES
    + MIP_VALIDATION_CASES
    + RNAFUSION_VALIDATION_CASES
    + TAXPROFILER_VALIDATION_CASES
)
